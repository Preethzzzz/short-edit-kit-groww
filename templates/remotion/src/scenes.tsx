import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {useBrand, useTone} from './brand';

// Background scenes, drawn in code (no logos or web photos). Colours come from the brand tones / theme.
// Add a new sector by writing one more scene here and registering it in SCENES.

const W = 1080;
const H = 1920;

const rand = (i: number) => {
	const x = Math.sin(i * 127.1 + 311.7) * 43758.5453;
	return x - Math.floor(x);
};

// Brand template A ground: off-white + faint dot grid (dark theme: deep radial).
export const Ground: React.FC<{children?: React.ReactNode}> = ({children}) => {
	const {theme} = useBrand();
	const tone = useTone();
	return (
		<AbsoluteFill style={{background: theme.dark ? `radial-gradient(ellipse at 50% 40%, ${theme.accentDark} 0%, ${theme.ground} 75%)` : theme.ground, color: theme.text}}>
			<AbsoluteFill style={{backgroundImage: `radial-gradient(${theme.dark ? 'rgba(255,255,255,0.10)' : tone('neutral').dark + '1A'} 2px, transparent 2px)`, backgroundSize: '40px 40px'}} />
			{children}
		</AbsoluteFill>
	);
};

const Sky: React.FC<{children: React.ReactNode; tint?: string}> = ({children, tint}) => {
	const {theme} = useBrand();
	const tone = useTone();
	const t = tint ?? theme.tint;
	return (
		<AbsoluteFill style={{background: `linear-gradient(180deg, ${theme.ground} 0%, ${t} 70%)`}}>
			<svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
				<defs>
					<pattern id="skydots" width="48" height="48" patternUnits="userSpaceOnUse">
						<circle cx="2" cy="2" r="2" fill={tone('neutral').main} opacity="0.10" />
					</pattern>
				</defs>
				<rect width={W} height={H} fill="url(#skydots)" />
				{children}
			</svg>
			{/* soft light behind the presenter so she separates from the scene */}
			<AbsoluteFill style={{background: 'radial-gradient(ellipse 46% 38% at 50% 72%, rgba(255,255,255,0.75) 0%, rgba(255,255,255,0) 70%)'}} />
		</AbsoluteFill>
	);
};

const Gear: React.FC<{cx: number; cy: number; r: number; teeth: number; angle: number; color: string; hole: string; opacity?: number}> = ({cx, cy, r, teeth, angle, color, hole, opacity = 1}) => {
	const pts: string[] = [];
	for (let i = 0; i < teeth * 2; i++) {
		const a = (i / (teeth * 2)) * Math.PI * 2;
		const rr = i % 2 === 0 ? r : r * 0.82;
		const a2 = a + Math.PI / (teeth * 2);
		pts.push(`${cx + rr * Math.cos(a)},${cy + rr * Math.sin(a)}`, `${cx + rr * Math.cos(a2)},${cy + rr * Math.sin(a2)}`);
	}
	return (
		<g transform={`rotate(${angle} ${cx} ${cy})`} opacity={opacity}>
			<polygon points={pts.join(' ')} fill={color} />
			<circle cx={cx} cy={cy} r={r * 0.42} fill={hole} />
			<circle cx={cx} cy={cy} r={r * 0.16} fill={color} />
		</g>
	);
};

// market: candles + rising line (intro, CTA, general market topics)
const Market: React.FC = () => {
	const frame = useCurrentFrame();
	const tone = useTone();
	const up = tone('profit').main;
	const down = tone('neutral').main;
	return (
		<Sky>
			{Array.from({length: 16}).map((_, i) => {
				const x = 30 + i * 66;
				const base = 1500 - i * 26 - rand(i) * 60;
				const h = 60 + rand(i + 9) * 120;
				const isUp = rand(i + 3) > 0.3;
				const show = interpolate(frame, [i * 3, i * 3 + 10], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
				return (
					<g key={i} opacity={0.5 * show}>
						<line x1={x + 18} y1={base - h - 30} x2={x + 18} y2={base + 30} stroke={isUp ? up : down} strokeWidth={4} />
						<rect x={x} y={base - h} width={36} height={h} rx={6} fill={isUp ? up : down} />
					</g>
				);
			})}
			<path d="M 0 1560 C 260 1500, 420 1420, 600 1330 S 900 1150, 1080 1080" fill="none" stroke={down} strokeWidth={6} opacity={0.35} strokeDasharray="2400" strokeDashoffset={interpolate(frame, [0, 60], [2400, 0], {extrapolateRight: 'clamp'})} />
		</Sky>
	);
};

// factory: roofs, supplier network with travelling pulses, gears (manufacturing)
const Factory: React.FC = () => {
	const frame = useCurrentFrame();
	const tone = useTone();
	const {theme} = useBrand();
	const n = tone('neutral');
	const nodes = [{x: 110, y: 1080}, {x: 250, y: 1240}, {x: 90, y: 1380}, {x: 970, y: 1050}, {x: 830, y: 1210}, {x: 990, y: 1360}];
	const links = [[0, 1], [1, 2], [3, 4], [4, 5], [1, 4]];
	return (
		<Sky>
			{[0, 1, 2, 3, 4, 5].map((i) => {
				const x = -40 + i * 200;
				return (
					<g key={i} fill={n.main} opacity={0.22}>
						<path d={`M ${x} 1720 L ${x} 1520 L ${x + 60} 1460 L ${x + 60} 1520 L ${x + 120} 1460 L ${x + 120} 1520 L ${x + 180} 1460 L ${x + 180} 1720 Z`} />
						{i % 2 === 0 ? <rect x={x + 140} y={1360} width={26} height={110} /> : null}
					</g>
				);
			})}
			{links.map(([a, b], i) => (
				<line key={i} x1={nodes[a].x} y1={nodes[a].y} x2={nodes[b].x} y2={nodes[b].y} stroke={n.main} strokeWidth={3} opacity={0.3} strokeDasharray="6 10" />
			))}
			{links.map(([a, b], i) => {
				const t = ((frame + i * 17) % 60) / 60;
				return <circle key={`p${i}`} cx={nodes[a].x + (nodes[b].x - nodes[a].x) * t} cy={nodes[a].y + (nodes[b].y - nodes[a].y) * t} r={8} fill={theme.accent} opacity={0.8} />;
			})}
			{nodes.map((p, i) => (
				<circle key={`n${i}`} cx={p.x} cy={p.y} r={16} fill={theme.ground} stroke={n.main} strokeWidth={5} />
			))}
			<Gear cx={70} cy={1640} r={90} teeth={10} angle={frame * 1.2} color={n.main} hole={theme.ground} opacity={0.45} />
			<Gear cx={1010} cy={1600} r={110} teeth={12} angle={-frame} color={n.dark} hole={theme.ground} opacity={0.35} />
		</Sky>
	);
};

const Turbine: React.FC<{x: number; base: number; h: number; angle: number; color: string}> = ({x, base, h, angle, color}) => {
	const hubY = base - h;
	return (
		<g>
			<path d={`M ${x - 10} ${base} L ${x - 4} ${hubY} L ${x + 4} ${hubY} L ${x + 10} ${base} Z`} fill={color} opacity={0.35} />
			<g transform={`rotate(${angle} ${x} ${hubY})`}>
				{[0, 120, 240].map((a) => (
					<path key={a} transform={`rotate(${a} ${x} ${hubY})`} d={`M ${x} ${hubY} Q ${x + 14} ${hubY - h * 0.25} ${x + 3} ${hubY - h * 0.52} Q ${x - 6} ${hubY - h * 0.26} ${x} ${hubY} Z`} fill={color} opacity={0.8} />
				))}
			</g>
			<circle cx={x} cy={hubY} r={9} fill={color} />
		</g>
	);
};

// gears: gears + wind turbines (industrial, power transmission, engineering, energy)
const Gears: React.FC = () => {
	const frame = useCurrentFrame();
	const tone = useTone();
	const {theme} = useBrand();
	const n = tone('neutral');
	return (
		<Sky>
			<Turbine x={930} base={1720} h={560} angle={frame * 2} color={n.main} />
			<Turbine x={1040} base={1720} h={420} angle={frame * 2.4 + 40} color={n.main} />
			<Turbine x={820} base={1720} h={330} angle={frame * 2.8 + 80} color={n.main} />
			<Gear cx={110} cy={1180} r={120} teeth={14} angle={frame * 1.1} color={n.main} hole={theme.ground} opacity={0.5} />
			<Gear cx={250} cy={1360} r={80} teeth={10} angle={-frame * 1.65 + 9} color={n.dark} hole={theme.ground} opacity={0.4} />
			<Gear cx={90} cy={1500} r={60} teeth={8} angle={frame * 2.2} color={n.main} hole={theme.ground} opacity={0.45} />
			<rect x={0} y={1720} width={W} height={200} fill={n.tint} opacity={0.8} />
		</Sky>
	);
};

const RadarDial: React.FC<{cx: number; cy: number; r: number; angle: number; line: string; sweep: string}> = ({cx, cy, r, angle, line, sweep}) => (
	<g>
		{[1, 0.72, 0.44].map((k) => (
			<circle key={k} cx={cx} cy={cy} r={r * k} fill="none" stroke={line} strokeWidth={3} opacity={0.35} />
		))}
		<line x1={cx - r} y1={cy} x2={cx + r} y2={cy} stroke={line} strokeWidth={2} opacity={0.3} />
		<line x1={cx} y1={cy - r} x2={cx} y2={cy + r} stroke={line} strokeWidth={2} opacity={0.3} />
		<path d={`M ${cx} ${cy} L ${cx + r} ${cy} A ${r} ${r} 0 0 0 ${cx + r * Math.cos(-0.6)} ${cy + r * Math.sin(-0.6)} Z`} fill={sweep} opacity={0.3} transform={`rotate(${angle} ${cx} ${cy})`} />
	</g>
);

// radar: radar sweeps + imaging band (defence, security, imaging)
const Radar: React.FC = () => {
	const frame = useCurrentFrame();
	const tone = useTone();
	const {theme} = useBrand();
	return (
		<Sky>
			<RadarDial cx={130} cy={1250} r={230} angle={frame * 3} line={tone('neutral').main} sweep={theme.accent} />
			<RadarDial cx={960} cy={1150} r={260} angle={-frame * 2.5 + 90} line={tone('neutral').main} sweep={theme.accent} />
			<defs>
				<linearGradient id="band" x1="0" x2="1">
					<stop offset="0" stopColor={tone('neutral').main} />
					<stop offset="1" stopColor={tone('neutral').dark} />
				</linearGradient>
			</defs>
			<rect x={0} y={1640} width={W} height={280} fill="url(#band)" opacity={0.25} />
		</Sky>
	);
};

// medical: heartbeat line, stent mesh, plus signs (healthcare, medical devices, pharma)
const Medical: React.FC = () => {
	const frame = useCurrentFrame();
	const tone = useTone();
	const n = tone('neutral').main;
	const beat = (x0: number) => `L ${x0} 1200 L ${x0 + 30} 1200 L ${x0 + 45} 1150 L ${x0 + 60} 1260 L ${x0 + 78} 1080 L ${x0 + 96} 1230 L ${x0 + 110} 1200`;
	let d = 'M -20 1200';
	for (let x = 0; x < W + 300; x += 300) d += ` L ${x + 150} 1200 ${beat(x + 150)}`;
	const offset = (frame * 6) % 300;
	return (
		<Sky>
			<g transform={`translate(${-offset} 0)`}>
				<path d={d} fill="none" stroke={n} strokeWidth={7} strokeLinejoin="round" opacity={0.45} />
			</g>
			<rect x={40} y={1380} width={160} height={360} rx={30} fill="none" stroke={n} strokeWidth={5} opacity={0.5} />
			{Array.from({length: 10}).map((_, i) => (
				<g key={i} stroke={n} strokeWidth={4} opacity={0.5}>
					<line x1={40} y1={1380 + i * 36} x2={200} y2={1416 + i * 36} />
					<line x1={200} y1={1380 + i * 36} x2={40} y2={1416 + i * 36} />
				</g>
			))}
			{[{x: 980, y: 1050}, {x: 900, y: 1450}, {x: 1010, y: 1600}].map((p, i) => (
				<g key={i} fill={n} opacity={0.4 + 0.2 * Math.sin(frame / 15 + i)}>
					<rect x={p.x - 10} y={p.y - 34} width={20} height={68} rx={4} />
					<rect x={p.x - 34} y={p.y - 10} width={68} height={20} rx={4} />
				</g>
			))}
		</Sky>
	);
};

// telecom: skyline, lattice towers with signal arcs, data link (telecom, internet, digital)
const Telecom: React.FC = () => {
	const frame = useCurrentFrame();
	const tone = useTone();
	const {theme} = useBrand();
	const n = tone('neutral');
	const drift = Math.sin(frame / 240) * 14;
	const skyline = (y: number, seed: number, minH: number, maxH: number, dx: number, op: number) => {
		const out: React.ReactNode[] = [];
		let x = -60;
		let i = 0;
		while (x < W + 60) {
			const w = 50 + rand(seed + i) * 90;
			const h = minH + rand(seed + i + 50) * (maxH - minH);
			out.push(<rect key={i} x={x} y={y - h} width={w - 6} height={h + 400} rx={4} />);
			x += w;
			i++;
		}
		return (
			<g fill={n.main} opacity={op} transform={`translate(${dx} 0)`}>
				{out}
			</g>
		);
	};
	const tower = (cx: number, baseY: number, topY: number, baseW: number, phase: number) => {
		const topW = baseW * 0.16;
		const hgt = baseY - topY;
		const legX = (t: number, s: number) => cx + s * (topW / 2 + (baseW / 2 - topW / 2) * t);
		const parts: React.ReactNode[] = [];
		for (let k = 0; k <= 11; k++) {
			const t = k / 11;
			const y = topY + hgt * t;
			parts.push(<line key={`r${k}`} x1={legX(t, -1)} y1={y} x2={legX(t, 1)} y2={y} strokeWidth={3} />);
			if (k < 11) {
				const t2 = (k + 1) / 11;
				const y2 = topY + hgt * t2;
				parts.push(<line key={`x${k}`} x1={legX(t, -1)} y1={y} x2={legX(t2, 1)} y2={y2} strokeWidth={2.2} />);
				parts.push(<line key={`y${k}`} x1={legX(t, 1)} y1={y} x2={legX(t2, -1)} y2={y2} strokeWidth={2.2} />);
			}
		}
		const arcs = [0, 1, 2].map((m) => {
			const p = ((frame + phase + m * 25) % 75) / 75;
			const r = 40 + p * 190;
			const ay = topY - 40;
			return (
				<g key={m} opacity={interpolate(p, [0, 0.15, 1], [0, 0.75, 0])} fill="none" stroke={theme.accent} strokeWidth={6} strokeLinecap="round">
					<path d={`M ${cx - r * 0.7} ${ay - r * 0.7} A ${r} ${r} 0 0 0 ${cx - r * 0.7} ${ay + r * 0.7}`} />
					<path d={`M ${cx + r * 0.7} ${ay - r * 0.7} A ${r} ${r} 0 0 1 ${cx + r * 0.7} ${ay + r * 0.7}`} />
				</g>
			);
		});
		return (
			<g key={cx}>
				{arcs}
				<g stroke={n.main}>
					<line x1={legX(1, -1)} y1={baseY} x2={legX(0, -1)} y2={topY} strokeWidth={6} />
					<line x1={legX(1, 1)} y1={baseY} x2={legX(0, 1)} y2={topY} strokeWidth={6} />
					{parts}
					<line x1={cx} y1={topY} x2={cx} y2={topY - 110} strokeWidth={5} />
				</g>
			</g>
		);
	};
	return (
		<Sky>
			{skyline(1560, 3, 180, 520, -drift * 0.5, 0.18)}
			{skyline(1700, 21, 120, 360, drift, 0.25)}
			<g opacity={0.8}>
				{tower(140, 1980, 760, 230, 0)}
				{tower(945, 1980, 640, 250, 37)}
			</g>
		</Sky>
	);
};

const Paper: React.FC = () => <Ground />;

export const SCENES: Record<string, React.FC> = {paper: Paper, market: Market, factory: Factory, gears: Gears, radar: Radar, medical: Medical, telecom: Telecom};
