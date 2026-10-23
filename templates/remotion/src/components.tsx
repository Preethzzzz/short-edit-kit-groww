import React from 'react';
import {Img, interpolate, staticFile, Easing} from 'remotion';
import {eio, eo, useBrand, useInk, useT, useTone} from './brand';
import {CountUp, fmt, Kicker, parseRich, Part, Pill, Rich, Stat} from './ui';

// Beat components. Every prop is data from edit.json; every `at` / `...At` is absolute seconds.
// Catalogue with props and examples: ../components.json. Content is sized for a ~900 px column;
// the Shell in Short.tsx puts it in a card (layout "card-top") or full-screen on the ground (layout "full").
// Tones: profit (green), loss (red), note (yellow), neutral (blue), accent (theme). Never decorative.

type At = number | undefined;

// ---------- text ----------

// Brand template A/B: line typed part by part in sync with VO, blur 8 -> 0, one accent phrase in italic serif.
export const KineticLine: React.FC<{parts: Part[]; size?: number}> = ({parts, size = 76}) => {
	const {frame, rel, ms} = useT();
	const ink = useInk();
	const tone = useTone();
	return (
		<div style={{textAlign: 'center', fontSize: size, lineHeight: 1.2, fontWeight: 500, letterSpacing: -1}}>
			{parseRich(parts).map((p, i) => {
				const k = eo(frame, rel(p.at, 0), rel(p.at, 0) + ms(300));
				return (
					<span key={i} style={{opacity: k, filter: `blur(${(1 - k) * 8}px)`, fontFamily: p.accent ? ink.serif : ink.sans, fontStyle: p.accent ? 'italic' : 'normal', color: p.accent ? tone(typeof p.accent === 'string' ? p.accent : 'accent').main : 'inherit', fontSize: p.accent ? size * 1.12 : size}}>
						{p.t}{' '}
					</span>
				);
			})}
		</div>
	);
};

// A note / important point (yellow = note by colour rule).
export const NoteCard: React.FC<{kicker?: string; text: string | Part[]; chips?: {text: string; at?: At}[]; tone?: string}> = ({kicker, text, chips = [], tone: t = 'note'}) => {
	const {enter, ms} = useT();
	const tone = useTone();
	const c = tone(t);
	return (
		<div style={{display: 'flex', flexDirection: 'column', gap: 28}}>
			{kicker ? <Kicker>{kicker}</Kicker> : null}
			<div style={{background: c.tint, borderLeft: `10px solid ${c.main}`, borderRadius: 22, padding: '26px 32px', opacity: enter(undefined, 0, 400)}}>
				<Rich text={text} size={46} />
			</div>
			<div style={{display: 'flex', gap: 16, flexWrap: 'wrap'}}>
				{chips.map((ch, i) => (
					<Pill key={i} text={ch.text} tone="neutral" k={enter(ch.at, ms(400) + i * ms(70))} />
				))}
			</div>
		</div>
	);
};

// ---------- numbers ----------

// One big number counting up to the script value (issue size, total bids...).
export const BigNumber: React.FC<{kicker?: string; label?: string; value: number; decimals?: number; prefix?: string; suffix?: string; tone?: string; note?: string; at?: At}> = ({kicker, label, value, decimals = 0, prefix = '', suffix = '', tone: t, note, at}) => {
	const {rel, enter, ms} = useT();
	const ink = useInk();
	const tone = useTone();
	return (
		<div style={{display: 'flex', flexDirection: 'column', gap: 18}}>
			{kicker ? <Kicker>{kicker}</Kicker> : null}
			{label ? <div style={{fontSize: 34, color: ink.sub, fontWeight: 500}}>{label}</div> : null}
			<div style={{fontSize: 140, fontWeight: 800, letterSpacing: -4, lineHeight: 1, color: t ? tone(t).dark : ink.text}}>
				<CountUp to={value} decimals={decimals} prefix={prefix} start={rel(at, 4)} dur={ms(900)} />
				<span style={{fontSize: 70, letterSpacing: 0}}>{suffix}</span>
			</div>
			{note ? <div style={{fontSize: 32, color: ink.sub, opacity: enter(at, 4, 900)}}>{note}</div> : null}
		</div>
	);
};

// Hook: combined total + stacked bar, each segment grows as its name is spoken.
export const StackedTotal: React.FC<{
	kicker?: string;
	label?: string;
	total: number;
	decimals?: number;
	prefix?: string;
	suffix?: string;
	items: {label: string; value: number; display: string; at?: At}[];
	footer?: {tag: string; text: string; at?: At};
}> = ({kicker, label, total, decimals = 0, prefix = '', suffix = '', items, footer}) => {
	const {frame, rel, ms, enter} = useT();
	const ink = useInk();
	const tone = useTone();
	const {brand} = useBrand();
	// Series colours identify items; they carry no profit/loss meaning.
	const segs = brand.series;
	const sum = items.reduce((s, x) => s + x.value, 0) || 1;
	return (
		<div style={{display: 'flex', flexDirection: 'column', gap: 28}}>
			{kicker ? <Kicker>{kicker}</Kicker> : null}
			<div>
				{label ? <div style={{fontSize: 34, color: ink.sub, fontWeight: 500}}>{label}</div> : null}
				<div style={{fontSize: 140, fontWeight: 800, letterSpacing: -4, lineHeight: 1}}>
					<CountUp to={total} decimals={decimals} prefix={prefix} start={4} dur={ms(900)} />
					<span style={{fontSize: 70, color: tone('accent').dark}}>{suffix}</span>
				</div>
			</div>
			<div style={{display: 'flex', height: 54, borderRadius: 12, overflow: 'hidden', background: ink.track}}>
				{items.map((x, i) => (
					<div key={i} style={{width: `${(x.value / sum) * 100 * eo(frame, rel(x.at, 0), rel(x.at, 0) + ms(500))}%`, background: segs[i % segs.length]}} />
				))}
			</div>
			<div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px 24px'}}>
				{items.map((x, i) => {
					const k = enter(x.at);
					return (
						<div key={i} style={{display: 'flex', alignItems: 'center', gap: 12, opacity: k, transform: `translateY(${(1 - k) * 16}px)`}}>
							<span style={{width: 22, height: 22, borderRadius: 6, background: segs[i % segs.length], flex: 'none'}} />
							<span style={{fontSize: 32, fontWeight: 700}}>{x.label}</span>
							<span style={{fontSize: 28, color: ink.sub}}>{x.display}</span>
						</div>
					);
				})}
			</div>
			{footer ? (
				<div style={{opacity: enter(footer.at), display: 'flex', alignItems: 'center', gap: 16, fontSize: 36, fontWeight: 700}}>
					<span style={{background: tone('neutral').main, color: ink.white, fontSize: 26, padding: '6px 14px', borderRadius: 10, letterSpacing: 1}}>{footer.tag}</span>
					{footer.text}
				</div>
			) : null}
		</div>
	);
};

// Two (or more) parts of one whole, e.g. Fresh issue vs OFS.
export const SplitBar: React.FC<{kicker?: string; total: number; parts: {label: string; value: number; display: string; note?: string; tone?: string; at?: At}[]}> = ({kicker, total, parts}) => {
	const {frame, rel, ms} = useT();
	const ink = useInk();
	const tone = useTone();
	return (
		<div style={{display: 'flex', flexDirection: 'column', gap: 28}}>
			{kicker ? <Kicker>{kicker}</Kicker> : null}
			<div style={{display: 'flex', height: 90, borderRadius: 16, overflow: 'hidden', background: ink.track}}>
				{parts.map((p, i) => (
					<div key={i} style={{width: `${(p.value / total) * 100 * eo(frame, rel(p.at, 6), rel(p.at, 6) + ms(600))}%`, background: tone(p.tone ?? (i ? 'neutral' : 'accent')).main}} />
				))}
			</div>
			<div style={{display: 'flex', justifyContent: 'space-between', gap: 24}}>
				{parts.map((p, i) => {
					const k = eo(frame, rel(p.at, 6), rel(p.at, 6) + ms(400));
					return (
						<div key={i} style={{opacity: k, textAlign: i === parts.length - 1 && i ? 'right' : 'left'}}>
							<div style={{fontSize: 30, fontWeight: 700, color: tone(p.tone ?? (i ? 'neutral' : 'accent')).dark}}>{p.label}</div>
							<div style={{fontSize: 64, fontWeight: 800}}>{p.display}</div>
							{p.note ? <div style={{fontSize: 28, color: ink.sub}}>{p.note}</div> : null}
						</div>
					);
				})}
			</div>
		</div>
	);
};

// Rows with amounts and bars (use of proceeds), optional source image panned so its amounts column is readable.
export const AmountRows: React.FC<{
	kicker?: string;
	max: number;
	rows: {label: string; value?: number; display?: string; tone?: string; at?: At}[];
	image?: {src: string; width: number; height: number; scale?: number; viewHeight?: number; at?: At};
}> = ({kicker, max, rows, image}) => {
	const {frame, rel, ms, dur} = useT();
	const ink = useInk();
	const tone = useTone();
	const pending = tone('note');
	let pan = 0;
	let k = 0;
	if (image) {
		const a = rel(image.at, 0);
		k = eo(frame, a, a + ms(400));
		pan = interpolate(frame, [a + 10, Math.max(a + 40, dur - 30)], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});
	}
	const sc = image?.scale ?? 0.75;
	return (
		<div style={{display: 'flex', flexDirection: 'column', gap: 26}}>
			{kicker ? <Kicker>{kicker}</Kicker> : null}
			{rows.map((r, i) => {
				const p = eo(frame, rel(r.at, 0), rel(r.at, 0) + ms(500));
				const c = tone(r.tone ?? 'neutral');
				return (
					<div key={i} style={{opacity: Math.max(0.15, p)}}>
						<div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 20}}>
							<span style={{fontSize: 32, fontWeight: 700}}>{r.label}</span>
							<span style={{fontSize: 44, fontWeight: 800, color: c.dark}}>{r.display ?? ''}</span>
						</div>
						<div style={{height: 26, borderRadius: 8, background: ink.track, marginTop: 8}}>
							<div style={{height: '100%', borderRadius: 8, width: `${r.value ? (r.value / max) * 100 * p : 100 * p}%`, background: r.value ? c.main : `repeating-linear-gradient(45deg, ${pending.main}, ${pending.main} 12px, ${pending.tint} 12px, ${pending.tint} 24px)`}} />
						</div>
					</div>
				);
			})}
			{image ? (
				<div style={{opacity: k, height: image.viewHeight ?? 300, overflow: 'hidden', borderRadius: 14, border: `2px solid ${ink.track}`, position: 'relative', background: ink.white}}>
					<Img src={staticFile(image.src)} style={{position: 'absolute', top: 0, left: 0, width: image.width * sc, height: image.height * sc, transform: `translateX(${-pan * Math.max(0, image.width * sc - 876)}px)`}} />
				</div>
			) : null}
		</div>
	);
};

// Flat bars growing from the baseline (brand template F).
export const Bars: React.FC<{title?: string | Part[]; bars: {label: string; value: number; display: string; tone?: string; at?: At}[]; max?: number; height?: number}> = ({title, bars, max, height = 560}) => {
	const {frame, rel, ms} = useT();
	const ink = useInk();
	const tone = useTone();
	const top = max ?? Math.max(...bars.map((b) => b.value)) * 1.1;
	return (
		<div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 50}}>
			{title ? <Rich text={title} size={58} style={{textAlign: 'center'}} /> : null}
			<div style={{display: 'flex', gap: bars.length > 3 ? 40 : 100, alignItems: 'flex-end'}}>
				{bars.map((b, i) => {
					const k = eo(frame, rel(b.at, ms(200) + i * ms(70)), rel(b.at, ms(200) + i * ms(70)) + ms(700));
					return (
						<div key={i} style={{display: 'flex', flexDirection: 'column', alignItems: 'center', width: bars.length > 3 ? 180 : 260}}>
							<div style={{fontSize: bars.length > 3 ? 56 : 90, fontWeight: 700, opacity: k}}>{b.display}</div>
							<div style={{width: bars.length > 3 ? 130 : 190, height, display: 'flex', alignItems: 'flex-end', background: ink.track, borderRadius: 20, overflow: 'hidden'}}>
								<div style={{width: '100%', height: `${(b.value / top) * 100 * k}%`, background: tone(b.tone ?? 'neutral').main, borderRadius: 20}} />
							</div>
							<div style={{fontSize: 32, fontWeight: 600, marginTop: 18, color: ink.sub, textAlign: 'center'}}>{b.label}</div>
						</div>
					);
				})}
			</div>
		</div>
	);
};

// a x b = result (lot size x upper band = minimum investment).
export const Calculation: React.FC<{kicker?: string; terms: {value: string; label: string}[]; op?: string; result: {label: string; value: string; at?: At}}> = ({kicker, terms, op = '×', result}) => {
	const {enter} = useT();
	const ink = useInk();
	const tone = useTone();
	const a = enter(undefined, 0, 400);
	const r = enter(result.at, 20, 400);
	return (
		<div style={{display: 'flex', flexDirection: 'column', gap: 30}}>
			{kicker ? <Kicker>{kicker}</Kicker> : null}
			<div style={{display: 'flex', alignItems: 'center', gap: 22, fontWeight: 800, opacity: a}}>
				{terms.map((t, i) => (
					<React.Fragment key={i}>
						{i ? <div style={{fontSize: 70, color: tone('accent').main}}>{op}</div> : null}
						<div style={{textAlign: 'center'}}>
							<div style={{fontSize: 96, lineHeight: 1}}>{t.value}</div>
							<div style={{fontSize: 28, color: ink.sub, fontWeight: 500}}>{t.label}</div>
						</div>
					</React.Fragment>
				))}
			</div>
			<div style={{opacity: r, transform: `translateY(${(1 - r) * 24}px)`, background: tone('neutral').main, color: ink.white, borderRadius: 24, padding: '24px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
				<span style={{fontSize: 36, fontWeight: 600}}>= {result.label}</span>
				<span style={{fontSize: 92, fontWeight: 800, letterSpacing: -2}}>{result.value}</span>
			</div>
		</div>
	);
};

// ---------- entities ----------

const Icon: React.FC<{name?: string; size: number}> = ({name, size}) => {
	const ink = useInk();
	const {frame} = useT();
	const tone = useTone();
	const n = tone('neutral').main;
	const acc = tone('accent').main;
	const s = {width: size, height: size};
	switch (name) {
		case 'factory':
			return (
				<svg {...s} viewBox="0 0 100 100">
					<path d="M8 88 V48 L30 60 V48 L52 60 V48 L74 60 V22 H90 V88 Z" fill={n} />
					<rect x="20" y="70" width="12" height="10" fill={ink.white} />
					<rect x="44" y="70" width="12" height="10" fill={ink.white} />
					<circle cx="82" cy="14" r={5 + 2 * Math.sin(frame / 8)} fill={acc} />
				</svg>
			);
		case 'gear':
			return (
				<svg {...s} viewBox="0 0 100 100">
					<g transform={`rotate(${frame * 2} 50 50)`}>
						{Array.from({length: 10}).map((_, i) => (
							<rect key={i} x="45" y="6" width="10" height="16" rx="2" fill={n} transform={`rotate(${i * 36} 50 50)`} />
						))}
						<circle cx="50" cy="50" r="30" fill={n} />
						<circle cx="50" cy="50" r="12" fill={ink.white} />
					</g>
				</svg>
			);
		case 'radar':
			return (
				<svg {...s} viewBox="0 0 100 100">
					<circle cx="50" cy="50" r="42" fill="none" stroke={n} strokeWidth="6" />
					<circle cx="50" cy="50" r="22" fill="none" stroke={n} strokeWidth="5" />
					<path d={`M50 50 L92 50 A42 42 0 0 0 ${50 + 42 * Math.cos(-0.7)} ${50 + 42 * Math.sin(-0.7)} Z`} fill={acc} opacity="0.7" transform={`rotate(${frame * 4} 50 50)`} />
					<circle cx="50" cy="50" r="6" fill={n} />
				</svg>
			);
		case 'heart':
			return (
				<svg {...s} viewBox="0 0 100 100">
					<path d="M50 88 C10 60 6 34 26 22 C38 15 48 22 50 30 C52 22 62 15 74 22 C94 34 90 60 50 88 Z" fill={n} />
					<path d="M14 54 H34 L40 42 L48 66 L56 46 L62 54 H86" fill="none" stroke={ink.white} strokeWidth="5" strokeLinejoin="round" />
				</svg>
			);
		case 'tower':
			return (
				<svg {...s} viewBox="0 0 100 100">
					<path d="M38 92 L47 30 H53 L62 92 M42 66 H58 M44 50 H56" stroke={n} strokeWidth="5" fill="none" />
					{[0, 1].map((m) => {
						const r = 12 + (((frame + m * 20) % 40) / 40) * 24;
						return <path key={m} d={`M ${50 - r} ${24 - r * 0.6} A ${r} ${r} 0 0 0 ${50 - r} ${24 + r * 0.6} M ${50 + r} ${24 - r * 0.6} A ${r} ${r} 0 0 1 ${50 + r} ${24 + r * 0.6}`} stroke={acc} strokeWidth="4" fill="none" opacity={1 - ((frame + m * 20) % 40) / 40} />;
					})}
				</svg>
			);
		case 'chart':
			return (
				<svg {...s} viewBox="0 0 100 100">
					{[30, 50, 42, 70].map((h, i) => (
						<rect key={i} x={10 + i * 22} y={90 - h} width="16" height={h} rx="3" fill={n} />
					))}
					<path d="M10 60 L32 44 L54 52 L86 20" stroke={acc} strokeWidth="5" fill="none" strokeDasharray="120" strokeDashoffset={interpolate(frame, [0, 30], [120, 0], {extrapolateRight: 'clamp'})} />
				</svg>
			);
		default:
			return null;
	}
};

// Company / fund card (redesigned X card): number, sector, name, icon, one-line business, stats as spoken.
export const EntityCard: React.FC<{
	number?: number | string;
	sector?: string;
	name: string;
	icon?: string;
	blurb?: string;
	stats: {label: string; value: string; tone?: string; big?: boolean; at?: At}[];
	badge?: {text: string; tone?: string; at?: At};
	footnote?: string;
}> = ({number, sector, name, icon, blurb, stats, badge, footnote}) => {
	const {frame, rel, ms, enter} = useT();
	const ink = useInk();
	const tone = useTone();
	const a = enter(undefined, 0, 400);
	let last = 0;
	return (
		<div style={{display: 'flex', flexDirection: 'column', gap: 26}}>
			<div style={{display: 'flex', alignItems: 'center', gap: 22, opacity: a}}>
				{number !== undefined ? (
					<div style={{width: 74, height: 74, borderRadius: 20, background: tone('accent').main, color: ink.white, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 46, fontWeight: 800, flex: 'none'}}>{number}</div>
				) : null}
				<div style={{flex: 1}}>
					{sector ? <div style={{fontSize: 26, fontWeight: 700, letterSpacing: 2, color: tone('neutral').main, textTransform: 'uppercase'}}>{sector}</div> : null}
					<div style={{fontSize: 44, fontWeight: 800, lineHeight: 1.1}}>{name}</div>
				</div>
				<Icon name={icon} size={110} />
			</div>
			{blurb ? <div style={{fontSize: 32, color: ink.sub, lineHeight: 1.3, opacity: a}}>{blurb}</div> : null}
			<div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16}}>
				{stats.map((s, i) => {
					// Stats without their own time follow the previous one by 1 s.
					const start = typeof s.at === 'number' ? rel(s.at) : last + ms(1000);
					last = start;
					return <Stat key={i} label={s.label} value={s.value} tone={s.tone} big={s.big} k={eo(frame, start, start + ms(350))} />;
				})}
			</div>
			{badge || footnote ? (
				<div style={{display: 'flex', gap: 14, alignItems: 'center', opacity: enter(badge?.at, last + ms(400))}}>
					{badge ? <Pill text={badge.text} tone={badge.tone ?? 'neutral'} solid /> : null}
					{footnote ? <span style={{fontSize: 28, color: ink.sub}}>{footnote}</span> : null}
				</div>
			) : null}
		</div>
	);
};

// Two flows side by side, e.g. Fresh issue (money to company) vs OFS (money to sellers); chips per item.
export const FlowExplainer: React.FC<{
	kicker?: string;
	chips?: {label: string; tone?: string; at?: At}[];
	lanes: {title: string; from: string; to: string; note?: string; tone?: string; at?: At}[];
	callout?: {big: string; text: string; tone?: string; at?: At};
}> = ({kicker, chips = [], lanes, callout}) => {
	const {frame, enter, ms} = useT();
	const ink = useInk();
	const tone = useTone();
	return (
		<div style={{display: 'flex', flexDirection: 'column', gap: 24}}>
			{kicker ? <Kicker>{kicker}</Kicker> : null}
			{chips.length ? (
				<div style={{display: 'flex', flexWrap: 'wrap', gap: 14}}>
					{chips.map((c, i) => (
						<Pill key={i} text={c.label} tone={c.tone ?? 'neutral'} k={enter(c.at, i * ms(70))} />
					))}
				</div>
			) : null}
			{lanes.map((l, i) => {
				const k = enter(l.at, ms(300) + i * ms(400), 400);
				const c = tone(l.tone ?? 'neutral');
				const t = (frame % 40) / 40;
				return (
					<div key={i} style={{opacity: k, transform: `translateX(${(1 - k) * -30}px)`, background: c.tint, borderRadius: 24, padding: '20px 26px'}}>
						<div style={{fontSize: 30, fontWeight: 800, color: c.dark, letterSpacing: 1}}>{l.title}</div>
						<div style={{display: 'flex', alignItems: 'center', gap: 16, marginTop: 10}}>
							<div style={{fontSize: 30, fontWeight: 700, width: 260}}>{l.from}</div>
							<div style={{position: 'relative', flex: 1, height: 6, background: c.main, borderRadius: 3}}>
								<div style={{position: 'absolute', top: -17, left: `${t * 88}%`, fontSize: 30, fontWeight: 800, color: c.dark}}>₹</div>
							</div>
							<div style={{fontSize: 30, fontWeight: 700, width: 240, textAlign: 'right'}}>{l.to}</div>
						</div>
						{l.note ? <div style={{fontSize: 28, color: ink.sub, marginTop: 8}}>{l.note}</div> : null}
					</div>
				);
			})}
			{callout ? (
				<div style={{opacity: enter(callout.at, ms(1500), 400), display: 'flex', alignItems: 'center', gap: 18, background: ink.text, color: ink.card, borderRadius: 20, padding: '16px 26px'}}>
					<span style={{fontSize: 70, fontWeight: 800, color: tone(callout.tone ?? 'note').main}}>{callout.big}</span>
					<span style={{fontSize: 32, fontWeight: 600, lineHeight: 1.2}}>{callout.text}</span>
				</div>
			) : null}
		</div>
	);
};

// ---------- lists ----------

export const Checklist: React.FC<{title?: string | Part[]; items: {text: string; at?: At}[]}> = ({title, items}) => {
	const {enter, ms} = useT();
	const ink = useInk();
	const tone = useTone();
	return (
		<div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 60}}>
			{title ? <Rich text={title} size={64} style={{textAlign: 'center'}} /> : null}
			<div style={{display: 'flex', flexDirection: 'column', gap: 30, width: '100%'}}>
				{items.map((it, i) => {
					const k = enter(it.at, ms(300) + i * ms(600), 350);
					return (
						<div key={i} style={{display: 'flex', alignItems: 'center', gap: 28, background: ink.card, borderRadius: 26, padding: '28px 32px', boxShadow: '0 14px 30px rgba(15,15,15,0.08)', opacity: k, transform: `scale(${0.9 + 0.1 * k})`}}>
							<div style={{width: 64, height: 64, borderRadius: 32, background: tone('neutral').main, color: ink.white, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 36, fontWeight: 800, flex: 'none'}}>{i + 1}</div>
							<div style={{fontSize: 42, fontWeight: 600, lineHeight: 1.2}}>{it.text}</div>
						</div>
					);
				})}
			</div>
		</div>
	);
};

// Rows that slide in one by one: "2023 | Small cap ahead | of large cap".
export const RowsReveal: React.FC<{title?: string | Part[]; rows: {lead: string; pill: string; note?: string; tone?: string; at?: At}[]}> = ({title, rows}) => {
	const {enter, ms} = useT();
	const ink = useInk();
	const tone = useTone();
	return (
		<div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 80}}>
			{title ? <Rich text={title} size={64} style={{textAlign: 'center'}} /> : null}
			<div style={{display: 'flex', flexDirection: 'column', gap: 40, width: '100%'}}>
				{rows.map((r, i) => {
					const k = enter(r.at, ms(300) + i * ms(600), 400);
					return (
						<div key={i} style={{display: 'flex', alignItems: 'center', gap: 30, opacity: Math.max(0.15, k), transform: `translateX(${(1 - k) * -40}px)`}}>
							<div style={{fontSize: 60, fontWeight: 700, minWidth: 170, color: tone('neutral').dark}}>{r.lead}</div>
							<Pill text={r.pill} tone={r.tone ?? 'neutral'} solid size={38} />
							{r.note ? <div style={{fontSize: 32, color: ink.sub}}>{r.note}</div> : null}
						</div>
					);
				})}
			</div>
		</div>
	);
};

export const Timeline: React.FC<{kicker?: string; items: {label: string; date: string; at?: At}[]}> = ({kicker, items}) => {
	const {frame, rel, enter, ms} = useT();
	const ink = useInk();
	const tone = useTone();
	return (
		<div style={{display: 'flex', flexDirection: 'column', gap: 28}}>
			{kicker ? <Kicker>{kicker}</Kicker> : null}
			<div style={{position: 'relative', paddingLeft: 70}}>
				<div style={{position: 'absolute', left: 22, top: 20, bottom: 20, borderLeft: `4px solid ${tone('neutral').main}`}} />
				{items.map((it, i) => {
					const k = enter(it.at, i * ms(500), 400);
					const on = frame >= rel(it.at, i * ms(500));
					return (
						<div key={i} style={{position: 'relative', marginBottom: 34, opacity: Math.max(0.15, k), transform: `translateX(${(1 - k) * 30}px)`}}>
							<div style={{position: 'absolute', left: -62, top: 14, width: 32, height: 32, borderRadius: 16, background: on ? tone('accent').main : ink.card, border: `4px solid ${on ? tone('accent').main : tone('neutral').main}`}} />
							<div style={{fontSize: 70, fontWeight: 800, lineHeight: 1}}>{it.date}</div>
							<div style={{fontSize: 34, color: ink.sub}}>{it.label}</div>
						</div>
					);
				})}
			</div>
		</div>
	);
};

// Document / report card sliding in with a slight 3D tilt, category pills popping in (brand template E).
export const DocCard: React.FC<{kicker?: string; title: string | Part[]; pills?: string[]; pillsAt?: At}> = ({kicker, title, pills = [], pillsAt}) => {
	const {frame, rel, ms} = useT();
	const ink = useInk();
	const tone = useTone();
	const card = eo(frame, 0, ms(400));
	return (
		<div style={{background: ink.card, borderRadius: 28, padding: '44px 50px', boxShadow: '0 30px 60px rgba(15,15,15,0.12)', transform: `perspective(1400px) rotateX(${(1 - card) * 8}deg) translateY(${(1 - card) * 60}px)`, opacity: card}}>
			{kicker ? <Kicker>{kicker}</Kicker> : null}
			<Rich text={title} size={58} style={{marginTop: 18}} />
			<div style={{display: 'flex', flexWrap: 'wrap', gap: 16, marginTop: 40}}>
				{pills.map((p, i) => {
					const k = eo(frame, rel(pillsAt, ms(600)) + i * ms(70), rel(pillsAt, ms(600)) + i * ms(70) + ms(300));
					return (
						<div key={i} style={{fontSize: 34, fontWeight: 600, padding: '12px 26px', borderRadius: 40, background: tone('neutral').tint, color: tone('neutral').dark, opacity: k, transform: `scale(${0.9 + 0.1 * k})`}}>
							{p}
						</div>
					);
				})}
			</div>
		</div>
	);
};

// ---------- data pictures ----------

// N tiles; at dropAt all but `keep` fall away in red (loss), kept ones turn green (stayed).
export const TileDrop: React.FC<{title: string | Part[]; count?: number; keep: number[]; dropAt?: At; result?: string | Part[]; sub?: string}> = ({title, count = 5, keep, dropAt, result, sub}) => {
	const {frame, rel, ms} = useT();
	const ink = useInk();
	const tone = useTone();
	const drop = rel(dropAt, ms(2000));
	const g = tone('profit');
	const r = tone('loss');
	const n = tone('neutral');
	return (
		<div style={{display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
			<Rich text={title} size={64} style={{textAlign: 'center'}} />
			<div style={{display: 'flex', gap: 26, marginTop: 120}}>
				{Array.from({length: count}).map((_, i) => {
					const k = eo(frame, ms(100) + i * ms(70), ms(400) + i * ms(70));
					const kept = keep.includes(i);
					const d = kept ? 0 : eio(frame, drop + i * ms(60), drop + i * ms(60) + ms(500));
					const after = frame > drop;
					const c = kept && after ? g : d > 0.5 ? r : n;
					return (
						<div key={i} style={{width: 160, height: 220, borderRadius: 26, background: kept && after ? g.main : d > 0.5 ? r.tint : ink.card, border: `4px solid ${c.main}`, opacity: k, transform: `translateY(${d * 260 + (1 - k) * 30}px) scale(${0.9 + 0.1 * k})`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 58, fontWeight: 700, color: kept && after ? ink.text : c.main}}>
							#{i + 1}
						</div>
					);
				})}
			</div>
			{result ? <Rich text={result} size={60} weight={700} style={{marginTop: 360, opacity: eo(frame, drop + ms(500), drop + ms(800)), textAlign: 'center'}} /> : null}
			{sub ? <div style={{fontSize: 34, color: ink.sub, marginTop: 14, opacity: eo(frame, drop + ms(500), drop + ms(800))}}>{sub}</div> : null}
		</div>
	);
};

// Grid of dots (default 100); at fadeAt all but `keep` fade, kept ones turn green.
export const DotGrid: React.FC<{title: string | Part[]; total?: number; keep: number[]; fadeAt?: At; result?: string | Part[]; sub?: string}> = ({title, total = 100, keep, fadeAt, result, sub}) => {
	const {frame, rel, ms} = useT();
	const ink = useInk();
	const tone = useTone();
	const fade = rel(fadeAt, ms(2000));
	const cols = Math.ceil(Math.sqrt(total));
	const n = tone('neutral');
	return (
		<div style={{display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
			<Rich text={title} size={60} style={{textAlign: 'center'}} />
			<div style={{display: 'grid', gridTemplateColumns: `repeat(${cols}, 52px)`, gap: 16, marginTop: 60}}>
				{Array.from({length: total}).map((_, i) => {
					const k = eo(frame, ms(60) + i * 0.5, ms(360) + i * 0.5);
					const kept = keep.includes(i);
					const f = kept ? 0 : eo(frame, fade + (i % cols) * 0.6, fade + (i % cols) * 0.6 + ms(400));
					const bg = kept && frame >= fade ? tone('profit').main : n.main;
					return <div key={i} style={{width: 52, height: 52, borderRadius: 26, background: bg, opacity: k * (1 - 0.8 * f), transform: `scale(${0.9 + 0.1 * k})`}} />;
				})}
			</div>
			{result ? <Rich text={result} size={64} weight={700} style={{marginTop: 50, opacity: eo(frame, fade + ms(500), fade + ms(800)), textAlign: 'center'}} /> : null}
			{sub ? <div style={{fontSize: 34, color: ink.sub, marginTop: 10, opacity: eo(frame, fade + ms(500), fade + ms(800))}}>{sub}</div> : null}
		</div>
	);
};

// Ranking shift: `mover` slides from rank `from` to rank `to` while others pass it; optional note card.
export const Ranking: React.FC<{title?: string | Part[]; items: string[]; mover: number; to: number; moverNote?: string; moveAt?: At; note?: {text: string; at?: At}}> = ({title, items, mover, to, moverNote, moveAt, note}) => {
	const {frame, rel, ms, enter} = useT();
	const ink = useInk();
	const tone = useTone();
	const m = rel(moveAt, ms(600));
	const p = eio(frame, m, m + ms(1600));
	const pos = (i: number) => {
		if (i === mover) return mover + (to - mover) * p;
		if (to > mover && i > mover && i <= to) return i - p;
		if (to < mover && i < mover && i >= to) return i + p;
		return i;
	};
	return (
		<div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 70}}>
			{title ? <Rich text={title} size={58} style={{textAlign: 'center'}} /> : null}
			<div style={{position: 'relative', width: 760, height: items.length * 130}}>
				{items.map((name, i) => (
					<div key={name} style={{position: 'absolute', left: 0, right: 0, top: pos(i) * 130, height: 106, borderRadius: 22, background: i === mover ? tone('neutral').tint : ink.card, border: `4px solid ${i === mover ? tone('neutral').main : ink.track}`, display: 'flex', alignItems: 'center', padding: '0 34px', justifyContent: 'space-between', fontSize: 40, fontWeight: 700}}>
						<span>#{Math.round(pos(i)) + 1} {name}</span>
						{i === mover && moverNote ? <span style={{fontSize: 30, color: tone('neutral').dark}}>{moverNote}</span> : null}
					</div>
				))}
			</div>
			{note ? (
				<div style={{width: '100%', background: tone('note').tint, border: `4px solid ${tone('note').main}`, borderRadius: 24, padding: '24px 34px', fontSize: 36, lineHeight: 1.3, opacity: enter(note.at, ms(2400), 400)}}>{note.text}</div>
			) : null}
		</div>
	);
};

// Screenshot / chart image with boxes on the rows being discussed and value tiles below (templates E/F).
export const ImageCallout: React.FC<{
	src: string;
	srcWidth: number;
	width?: number;
	highlights?: {x: number; y: number; w: number; h: number; tone?: string; at?: At}[];
	tiles?: {label: string; value: string; note?: string; tone?: string; at?: At}[];
}> = ({src, srcWidth, width = 900, highlights = [], tiles = []}) => {
	const {frame, rel, ms} = useT();
	const ink = useInk();
	const tone = useTone();
	const card = eo(frame, 0, ms(400));
	const sc = width / srcWidth;
	return (
		<div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 50}}>
			<div style={{position: 'relative', width, borderRadius: 18, overflow: 'hidden', boxShadow: '0 30px 60px rgba(15,15,15,0.14)', background: ink.white, opacity: card, transform: `perspective(1400px) rotateX(${(1 - card) * 8}deg)`}}>
				<Img src={staticFile(src)} style={{width, display: 'block'}} />
				{highlights.map((h, i) => {
					const k = eo(frame, rel(h.at, ms(600)), rel(h.at, ms(600)) + ms(400));
					const c = tone(h.tone ?? 'neutral').main;
					return <div key={i} style={{position: 'absolute', left: h.x * sc, top: h.y * sc, height: h.h * sc, width: h.w * sc * k, border: `4px solid ${c}`, borderRadius: 10, boxShadow: `0 0 0 4px ${c}33`}} />;
				})}
			</div>
			{tiles.length ? (
				<div style={{display: 'flex', gap: 30}}>
					{tiles.map((t, i) => {
						const k = eo(frame, rel(t.at, ms(800)) + ms(200), rel(t.at, ms(800)) + ms(500));
						const c = tone(t.tone ?? 'neutral');
						return (
							<div key={i} style={{opacity: k, background: ink.card, borderRadius: 24, padding: '20px 30px', border: `4px solid ${c.main}`, textAlign: 'center'}}>
								<div style={{fontSize: 30, color: ink.sub, fontWeight: 600}}>{t.label}</div>
								<div style={{fontSize: 80, fontWeight: 800, color: c.dark}}>{t.value}</div>
								{t.note ? <div style={{fontSize: 28, color: ink.sub}}>{t.note}</div> : null}
							</div>
						);
					})}
				</div>
			) : null}
		</div>
	);
};

// Article / clipping screenshot as a clean card; highlighter wipes across a phrase (template E).
export const ImageCard: React.FC<{src: string; width: number; height: number; caption?: string; highlight?: {x: number; y: number; w: number; h: number; tone?: string; at?: At}}> = ({src, width, height, caption, highlight}) => {
	const {frame, rel, ms} = useT();
	const ink = useInk();
	const tone = useTone();
	const card = eo(frame, 0, ms(400));
	const w = Math.min(900, width);
	const sc = w / width;
	const hk = highlight ? eo(frame, rel(highlight.at, ms(500)), rel(highlight.at, ms(500)) + ms(400)) : 0;
	return (
		<div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 24}}>
			<div style={{position: 'relative', width: w, height: height * sc, background: ink.white, borderRadius: 16, overflow: 'hidden', boxShadow: '0 24px 50px rgba(15,15,15,0.14)', opacity: card, transform: `perspective(1400px) rotateY(${(1 - card) * 8}deg)`}}>
				{highlight ? <div style={{position: 'absolute', left: highlight.x * sc, top: highlight.y * sc, height: highlight.h * sc, width: highlight.w * sc * hk, background: tone(highlight.tone ?? 'note').main, opacity: 0.6}} /> : null}
				<Img src={staticFile(src)} style={{position: 'absolute', inset: 0, width: w, height: height * sc, mixBlendMode: 'multiply'}} />
			</div>
			{caption ? <div style={{fontSize: 32, color: ink.sub, textAlign: 'center'}}>{caption}</div> : null}
		</div>
	);
};

export const COMPONENTS: Record<string, React.FC<any>> = {
	KineticLine, NoteCard, BigNumber, StackedTotal, SplitBar, AmountRows, Bars, Calculation, EntityCard, FlowExplainer,
	Checklist, RowsReveal, Timeline, DocCard, TileDrop, DotGrid, Ranking, ImageCallout, ImageCard,
};
