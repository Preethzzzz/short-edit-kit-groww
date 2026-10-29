import React from 'react';
import {AbsoluteFill, Audio, Easing, Img, interpolate, OffthreadVideo, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {BrandCtx, CueCtx, eo, useBrand, useInk} from './brand';
import {COMPONENTS} from './components';
import {CUSTOM, CUSTOM_SCENES} from './custom';
import {Ground, SCENES} from './scenes';
import type {Cue, EditProps} from './types';
import {SourceTag} from './ui';

// One generic Short, driven entirely by edit.json (see scripts/build_plan.py).
// layout "card-top": presenter on a scene background, cards in the top area, presenter drops while a card is up.
// layout "full": cards replace the A-roll full-screen; talk stretches switch WIDE / MCU framing.

const CENTERED = new Set(['KineticLine']);
const ALL: Record<string, React.FC<any>> = {...COMPONENTS, ...CUSTOM};
const ALL_SCENES: Record<string, React.FC> = {...SCENES, ...CUSTOM_SCENES};

const useF = () => {
	const {fps} = useVideoConfig();
	return (s: number) => Math.round(s * fps);
};

// 0..1: how much a top card is on screen (ease-out in, fade out), used to move presenter and captions.
const useCardAmount = (cues: Cue[]) => {
	const frame = useCurrentFrame();
	const f = useF();
	const {brand} = useBrand();
	const inF = f(brand.motion.cardInMs / 1000);
	let v = 0;
	for (const c of cues) {
		const a = f(c.from);
		const b = f(c.to);
		if (frame < a - inF || frame > b + inF) continue;
		v = Math.max(v, Math.min(eo(frame, a - 4, a - 4 + inF), 1 - eo(frame, b, b + inF)));
	}
	return v;
};

const Background: React.FC<{p: EditProps}> = ({p}) => {
	const frame = useCurrentFrame();
	const f = useF();
	const x = f(p.brand.motion.sceneCrossfadeSec);
	if (!p.sections.length) return <Ground />;
	return (
		<AbsoluteFill>
			{p.sections.map((s, i) => {
				const a = f(s.from);
				const b = i + 1 < p.sections.length ? f(p.sections[i + 1].from) : 1e9;
				if (frame < a - x || frame > b + x) return null;
				const o = interpolate(frame, [a - x, a, b, b + x], [i === 0 ? 1 : 0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
				const Scene = ALL_SCENES[s.scene] ?? SCENES.paper;
				return (
					<AbsoluteFill key={i} style={{opacity: o}}>
						<Sequence from={a - x} layout="none">
							<Scene />
						</Sequence>
					</AbsoluteFill>
				);
			})}
		</AbsoluteFill>
	);
};

const Presenter: React.FC<{p: EditProps; topCues: Cue[]}> = ({p, topCues}) => {
	const frame = useCurrentFrame();
	const f = useF();
	const g = useCardAmount(topCues);
	if (!p.presenter) return null;
	const t = frame / f(1);
	let z = 1;
	for (const zm of p.zooms) {
		const a = f(zm.from);
		const b = f(zm.to);
		const k = interpolate(frame, [a, a + 8, b - 8, b], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});
		z = Math.max(z, 1 + (zm.scale - 1) * k);
	}
	let framing = 1;
	if (p.layout === 'full') {
		const cur = [...p.talk].reverse().find((x) => t >= x.from);
		framing = cur?.framing === 'MCU' ? p.brand.framing.mcu : 1;
	}
	const punch = [...p.punches].reverse().find((x) => t >= x.from)?.scale ?? 1;
	const scale = z * (1 - 0.06 * g) * punch;
	const {presenter} = p;
	return (
		<AbsoluteFill style={{transform: `translateY(${g * p.brand.layout.presenterDrop}px) scale(${scale * framing})`, transformOrigin: p.layout === 'full' ? '50% 30%' : '50% 45%'}}>
			{p.segments.map((s) => (
				<Sequence key={s.out} from={f(s.out)} durationInFrames={Math.max(1, f(s.out + s.src1 - s.src0) - f(s.out))} layout="none">
					<AbsoluteFill style={{transform: `scale(${s.punch ?? 1})`, transformOrigin: '50% 40%'}}>
						<OffthreadVideo src={staticFile(presenter.src)} startFrom={f(s.src0 - presenter.offset)} transparent muted style={{width: '100%', height: '100%'}} />
					</AbsoluteFill>
				</Sequence>
			))}
		</AbsoluteFill>
	);
};

const Shell: React.FC<{cue: Cue; layout: 'card-top' | 'full'}> = ({cue, layout}) => {
	const frame = useCurrentFrame();
	const f = useF();
	const {brand, theme} = useBrand();
	const ink = useInk();
	const dur = f(cue.to) - f(cue.from);
	const C = ALL[cue.component];
	if (!C) return null;
	const inK = eo(frame, 0, f(brand.motion.cardInMs / 1000));
	const outK = interpolate(frame, [dur - f(brand.motion.fadeOutMs / 1000), dur], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	// Brand: never a static hold; slow push-in while the card is up.
	const push = 1 + (brand.motion.pushInPct / 100) * interpolate(frame, [0, Math.max(1, dur)], [0, 1], {extrapolateRight: 'clamp'});
	const L = brand.layout;
	const body = (
		<CueCtx.Provider value={{from: cue.from, to: cue.to}}>
			<C {...cue.props} />
		</CueCtx.Provider>
	);
	if (layout === 'full') {
		return (
			<AbsoluteFill style={{fontFamily: ink.sans, color: ink.text}}>
				<Ground />
				<div style={{position: 'absolute', top: L.cardTop + 40, bottom: 1920 - L.captionTop + 30, left: L.safe.left, right: 1080 - L.safe.right, display: 'flex', flexDirection: 'column', justifyContent: CENTERED.has(cue.component) ? 'center' : 'flex-start', opacity: outK, transform: `scale(${push})`}}>
					{body}
				</div>
				{cue.source ? <SourceTag text={cue.source} dark={theme.dark} /> : null}
			</AbsoluteFill>
		);
	}
	return (
		<>
			<div style={{position: 'absolute', top: L.cardTop, left: 50, width: 980, height: L.cardBottom - L.cardTop, display: 'flex', flexDirection: 'column', justifyContent: 'center', opacity: Math.min(inK, outK), transform: `translateY(${(1 - inK) * 40}px) scale(${(0.97 + 0.03 * inK) * push})`, fontFamily: ink.sans, color: ink.text}}>
				<div style={{background: ink.card, borderRadius: 40, padding: 52, boxShadow: '0 24px 60px rgba(20,22,31,0.10), 0 2px 6px rgba(20,22,31,0.06)', borderTop: `12px solid ${theme.accent}`}}>{body}</div>
			</div>
			{cue.source ? <div style={{opacity: Math.min(inK, outK)}}><SourceTag text={cue.source} dark={theme.dark} /></div> : null}
		</>
	);
};

const Captions: React.FC<{p: EditProps; topCues: Cue[]}> = ({p, topCues}) => {
	const frame = useCurrentFrame();
	const f = useF();
	const g = useCardAmount(topCues);
	const t = frame / f(1);
	const c = p.captions.find((x) => t >= x.from && t < x.to);
	if (!c) return null;
	const L = p.brand.layout;
	const s = p.brand.captions;
	const k = eo(frame, f(c.from), f(c.from) + f(0.15));
	// A bottom end card takes the caption slot: captions sit at the with-card height while it shows.
	const endBottom = p.endCard?.position === 'bottom' ? eo(frame, f(p.endCard.from), f(p.endCard.from) + f(0.4)) : 0;
	const top = interpolate(Math.max(g, endBottom), [0, 1], [L.captionTop, L.captionTopWithCard]);
	// Word-by-word highlight: the spoken word's slot (starts[] from build_plan) is shown in the accent colour.
	const words = c.text.split(' ');
	let active = -1;
	(c.starts ?? []).forEach((st, i) => {
		if (t >= st) active = i;
	});
	return (
		<div style={{position: 'absolute', left: L.safe.left, width: L.safe.right - L.safe.left, top, display: 'flex', justifyContent: 'center'}}>
			<div style={{fontFamily: p.brand.fonts.sans, fontSize: s.size, fontWeight: s.weight, lineHeight: 1.25, color: s.color, background: s.bg, borderRadius: s.radius, padding: '14px 26px', textAlign: 'center', opacity: k, transform: `translateY(${(1 - k) * 8}px)`}}>
				{words.map((w, i) => (
					<span key={i} style={{color: i === active ? s.activeColor : s.color}}>
						{w}
						{i < words.length - 1 ? ' ' : ''}
					</span>
				))}
			</div>
		</div>
	);
};

const Header: React.FC<{p: EditProps; dark: boolean}> = ({p, dark}) => {
	const ink = useInk();
	const {brand} = p;
	const L = brand.logo;
	return (
		<>
			{p.header.tag || p.header.topic ? (
				<div style={{position: 'absolute', top: L.top, left: brand.layout.safe.left, fontFamily: brand.fonts.sans, display: 'flex', gap: 14, alignItems: 'center', maxWidth: 1080 - L.width - L.right - brand.layout.safe.left - 30}}>
					{p.header.tag ? <div style={{background: brand.tones.neutral.main, color: ink.white, fontWeight: 800, fontSize: 28, padding: '10px 18px', borderRadius: 10, letterSpacing: 1, whiteSpace: 'nowrap'}}>{p.header.tag}</div> : null}
					{p.header.topic ? <div style={{fontSize: 28, fontWeight: 700, color: dark ? ink.white : p.theme.text}}>{p.header.topic}</div> : null}
				</div>
			) : null}
			<Img src={staticFile(dark ? L.onDark : L.onLight)} style={{position: 'absolute', top: L.top, right: L.right, width: L.width}} />
		</>
	);
};

const OpeningLines: React.FC<{p: EditProps}> = ({p}) => {
	const frame = useCurrentFrame();
	const f = useF();
	const c = p.brand.compliance;
	if (!c.openingLines.length) return null;
	const end = f(c.openingSeconds);
	const o = interpolate(frame, [0, 5, end - 6, end], [0, 1, 1, 0], {extrapolateRight: 'clamp'});
	if (o <= 0) return null;
	return (
		<div style={{position: 'absolute', top: p.brand.layout.headerBandBottom - 10, left: p.brand.layout.safe.left, right: p.brand.logo.right, textAlign: 'right', fontFamily: p.brand.fonts.sans, fontSize: 21, lineHeight: 1.35, color: p.theme.dark ? 'rgba(255,255,255,0.75)' : p.brand.palette.sub, opacity: o}}>
			{c.openingLines.map((l) => (
				<div key={l}>{l}</div>
			))}
		</div>
	);
};

// Disclaimer card: yellow accent = disclaimer / note (colour rule).
const EndCard: React.FC<{p: EditProps}> = ({p}) => {
	const frame = useCurrentFrame();
	const f = useF();
	if (!p.endCard) return null;
	const k = eo(frame, f(p.endCard.from), f(p.endCard.from) + f(0.4));
	if (k <= 0) return null;
	const L = p.brand.layout;
	const place = p.endCard.position === 'bottom' ? {bottom: 1920 - L.safe.bottom} : {top: L.cardTop};
	if (p.endCard.raBox) {
		// Brand RA box: centred white lines on the neutral blue.
		return (
			<div style={{position: 'absolute', ...place, left: L.safe.left, right: 1080 - L.safe.right, opacity: k, transform: `translateY(${(1 - k) * 12}px)`, fontFamily: p.brand.fonts.sans, color: p.brand.palette.white, background: p.brand.tones.neutral.main, borderRadius: 22, padding: '22px 26px', fontSize: 33, fontWeight: 600, lineHeight: 1.38, textAlign: 'center', boxShadow: '0 16px 36px rgba(15,15,15,0.18)'}}>
				{p.endCard.raBox.map((l) => (
					<div key={l}>{l}</div>
				))}
			</div>
		);
	}
	return (
		<div style={{position: 'absolute', ...(p.endCard.position === 'bottom' ? {bottom: 1920 - L.safe.bottom} : {top: L.cardTop}), left: L.safe.left, right: 1080 - L.safe.right - 60, opacity: k, transform: `translateY(${(1 - k) * 12}px)`, fontFamily: p.brand.fonts.sans, color: p.brand.palette.ink, background: p.brand.palette.white, borderLeft: `10px solid ${p.brand.tones.note.main}`, borderRadius: 22, padding: '24px 30px', fontSize: 25, lineHeight: 1.4, boxShadow: '0 16px 36px rgba(15,15,15,0.10)'}}>
			{p.endCard.text}
			<div style={{marginTop: 10, fontWeight: 700}}>{p.endCard.ra}</div>
		</div>
	);
};

export const Short: React.FC<EditProps> = (p) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const t = frame / fps;
	const f = (s: number) => Math.round(s * fps);
	const topCues = p.layout === 'card-top' ? p.cues : [];
	const fullCue = p.layout === 'full' ? p.cues.find((c) => t >= c.from && t < c.to) : undefined;
	const dark = p.theme.dark;
	return (
		<BrandCtx.Provider value={{brand: p.brand, theme: p.theme}}>
			<AbsoluteFill style={{background: p.theme.ground}}>
				<Background p={p} />
				{fullCue ? null : <Presenter p={p} topCues={topCues} />}
				{p.cues.map((c) => (
					<Sequence key={c.id + c.from} from={f(c.from)} durationInFrames={Math.max(1, f(c.to) - f(c.from))} layout="none">
						<Shell cue={c} layout={p.layout} />
					</Sequence>
				))}
				<Captions p={p} topCues={topCues} />
				<Header p={p} dark={dark} />
				<OpeningLines p={p} />
				<EndCard p={p} />
				{p.mix || p.voice ? <Audio src={staticFile((p.mix ?? p.voice) as string)} /> : null}
			</AbsoluteFill>
		</BrandCtx.Provider>
	);
};
