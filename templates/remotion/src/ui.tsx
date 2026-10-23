import React from 'react';
import {interpolate, useCurrentFrame, Easing} from 'remotion';
import {useBrand, useInk, useTone} from './brand';

// Indian digit grouping, fixed decimals.
export const fmt = (n: number, d = 2) => n.toLocaleString('en-IN', {minimumFractionDigits: d, maximumFractionDigits: d});

// Rich line: "plain words *accent phrase* more" -> accent phrase in italic serif, theme accent colour.
// Brand: sans line + one emphasised phrase in italic serif. Use {tone} objects for profit/loss emphasis.
export type Part = string | {t: string; accent?: boolean | string; at?: number};
export const parseRich = (x: string | Part[]): {t: string; accent?: boolean | string; at?: number}[] => {
	if (Array.isArray(x)) return x.map((p) => (typeof p === 'string' ? {t: p} : p));
	return x
		.split(/(\*[^*]+\*)/)
		.filter(Boolean)
		.map((s) => (s.startsWith('*') && s.endsWith('*') ? {t: s.slice(1, -1), accent: true} : {t: s}));
};

export const Rich: React.FC<{text: string | Part[]; size?: number; weight?: number; style?: React.CSSProperties}> = ({text, size = 60, weight = 600, style}) => {
	const ink = useInk();
	const tone = useTone();
	return (
		<div style={{fontSize: size, fontWeight: weight, lineHeight: 1.2, letterSpacing: -0.5, ...style}}>
			{parseRich(text).map((p, i) => (
				<span key={i} style={p.accent ? {fontFamily: ink.serif, fontStyle: 'italic', fontWeight: 500, color: tone(typeof p.accent === 'string' ? p.accent : 'accent').main} : undefined}>
					{p.t}
				</span>
			))}
		</div>
	);
};

export const Kicker: React.FC<{children: React.ReactNode}> = ({children}) => {
	const tone = useTone();
	return <div style={{fontSize: 30, fontWeight: 700, letterSpacing: 3, textTransform: 'uppercase', color: tone('accent').main}}>{children}</div>;
};

export const CountUp: React.FC<{to: number; decimals?: number; start?: number; dur?: number; prefix?: string; suffix?: string}> = ({to, decimals = 0, start = 0, dur = 24, prefix = '', suffix = ''}) => {
	const frame = useCurrentFrame();
	const v = interpolate(frame, [start, start + dur], [0, to], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
	// Land exactly on the script value.
	const shown = frame >= start + dur ? to : v;
	return (
		<span style={{fontVariantNumeric: 'tabular-nums'}}>
			{prefix}
			{fmt(shown, decimals)}
			{suffix}
		</span>
	);
};

export const Stat: React.FC<{label: string; value: string; k: number; big?: boolean; tone?: string}> = ({label, value, k, big, tone: t}) => {
	const ink = useInk();
	const tone = useTone();
	return (
		<div style={{opacity: k, transform: `translateY(${(1 - k) * 18}px)`, background: ink.track, borderRadius: 18, padding: '14px 20px'}}>
			<div style={{fontSize: 26, color: ink.sub, fontWeight: 600}}>{label}</div>
			<div style={{fontSize: big ? 56 : 44, fontWeight: 800, color: t ? tone(t).dark : ink.text, lineHeight: 1.1, letterSpacing: -1}}>{value}</div>
		</div>
	);
};

export const Pill: React.FC<{text: string; tone?: string; k?: number; solid?: boolean; size?: number}> = ({text, tone: t = 'neutral', k = 1, solid, size = 30}) => {
	const tone = useTone();
	const ink = useInk();
	const c = tone(t);
	return (
		<span style={{display: 'inline-block', fontSize: size, fontWeight: 700, padding: '8px 22px', borderRadius: 40, background: solid ? c.main : c.tint, color: solid ? (t === 'neutral' || t === 'loss' ? ink.white : ink.text) : c.dark, border: `3px solid ${c.main}`, opacity: k, transform: `scale(${0.9 + 0.1 * k})`}}>
			{text}
		</span>
	);
};

// Brand: "Source: X" credit, small sans, top-right under the logo.
export const SourceTag: React.FC<{text: string; dark?: boolean}> = ({text, dark}) => {
	const {brand} = useBrand();
	return (
		<div style={{position: 'absolute', right: brand.logo.right, top: brand.layout.sourceTop, fontFamily: brand.fonts.sans, fontSize: 24, color: dark ? 'rgba(255,255,255,0.75)' : brand.palette.sub, textAlign: 'right', maxWidth: 700}}>
			Source: {text}
		</div>
	);
};
