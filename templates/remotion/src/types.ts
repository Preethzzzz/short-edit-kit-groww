// Shape of edit.json (the props of the Short composition), produced by scripts/build_plan.py.

export type Tone = {main: string; dark: string; tint: string; means?: string};
export type Theme = {ground: string; tint: string; accent: string; accentDark: string; text: string; dark: boolean};

export type Brand = {
	name: string;
	palette: Record<string, string>;
	series: string[]; // item-identity colours (stacked bars), carry no profit/loss meaning
	tones: {profit: Tone; loss: Tone; note: Tone; neutral: Tone};
	fonts: {sans: string; serif: string};
	logo: {onLight: string; onDark: string; width: number; right: number; top: number};
	layout: {
		headerBandBottom: number;
		safe: {left: number; right: number; top: number; bottom: number};
		cardTop: number;
		cardBottom: number;
		captionTop: number;
		captionTopWithCard: number;
		presenterDrop: number;
		sourceTop: number;
	};
	motion: {cardInMs: number; itemInMs: number; staggerMs: number; fadeOutMs: number; pushInPct: number; sceneCrossfadeSec: number};
	captions: {bg: string; color: string; size: number; weight: number; radius: number; activeColor: string};
	framing: {mcu: number; punch: number};
	compliance: {openingLines: string[]; openingSeconds: number};
};

// Matches the keyed presenter to a photo background: CSS filter values + a soft rim of the background's light.
export type PresenterLook = {brightness?: number; contrast?: number; saturate?: number; hue?: number; rim?: string | null; rimPx?: number};

export type Segment = {src0: number; src1: number; out: number; punch?: number};
export type Cue = {id: string; component: string; from: number; to: number; source?: string | null; props: Record<string, any>};
export type Caption = {from: number; to: number; text: string; starts?: number[]};

export type EditProps = {
	fps: number;
	width: number;
	height: number;
	duration: number;
	layout: 'card-top' | 'full';
	brand: Brand;
	theme: Theme;
	header: {tag?: string | null; topic?: string | null};
	presenter: {src: string; offset: number; look?: PresenterLook} | null;
	// scene "photo": one still behind the keyed presenter for the whole video (format explainer-story)
	// where/when the SEBI lines show (text always comes from the brand pack)
	sebi?: {position?: 'top' | 'bottom'; openingSeconds?: number; closingSeconds?: number} | null;
	background?: {src: string; blur?: number; dim?: number; drift?: number; dark?: boolean} | null;
	voice: string | null;
	mix: string | null; // voice + bed + effects (scripts/build_mix.py); played instead of voice when set
	punches: {from: number; scale: number}[]; // cut-style framing changes on the presenter
	segments: Segment[];
	sections: {scene: string; from: number}[];
	talk: {from: number; framing: 'WIDE' | 'MCU'}[];
	cues: Cue[];
	captions: Caption[];
	zooms: {from: number; to: number; scale: number}[];
	endCard: {from: number; text: string; ra: string; position?: 'top' | 'bottom'; raBox?: string[]} | null;
};
