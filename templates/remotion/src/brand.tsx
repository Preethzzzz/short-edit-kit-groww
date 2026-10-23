import React, {createContext, useContext} from 'react';
import {Easing, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Brand, Theme} from './types';

// Everything visual comes from the brand pack (brand.json, injected by build_plan.py). No colours live here.

export const BrandCtx = createContext<{brand: Brand; theme: Theme}>(null as never);
export const useBrand = () => useContext(BrandCtx);

export type ToneName = 'profit' | 'loss' | 'note' | 'neutral' | 'accent';
export type ToneSet = {main: string; dark: string; tint: string};

export const useTone = () => {
	const {brand, theme} = useBrand();
	return (t?: string): ToneSet => {
		if (t === 'accent') return {main: theme.accent, dark: theme.accentDark, tint: theme.tint};
		const x = brand.tones[(t as keyof Brand['tones']) ?? 'neutral'] ?? brand.tones.neutral;
		return {main: x.main, dark: x.dark, tint: x.tint};
	};
};

// Card surface + text colours for the current theme.
export const useInk = () => {
	const {brand, theme} = useBrand();
	return {
		card: theme.dark ? theme.tint : brand.palette.white,
		white: brand.palette.white,
		text: theme.text,
		sub: theme.dark ? 'rgba(248,248,248,0.72)' : brand.palette.sub,
		track: theme.dark ? 'rgba(255,255,255,0.10)' : brand.palette.track,
		ground: theme.ground,
		sans: brand.fonts.sans,
		serif: brand.fonts.serif,
	};
};

// Brand motion: ease-out cubic, no overshoot. Never spring/bounce.
export const eo = (frame: number, a: number, b: number) =>
	interpolate(frame, [a, Math.max(a + 1, b)], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
export const eio = (frame: number, a: number, b: number) =>
	interpolate(frame, [a, Math.max(a + 1, b)], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});

// Cue-relative timing. `at` values in props are absolute seconds (resolved from script phrases by build_plan.py).
export const CueCtx = createContext<{from: number; to: number}>({from: 0, to: 0});
export const useT = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const {from, to} = useContext(CueCtx);
	const {brand} = useBrand();
	const ms = (m: number) => Math.round((m / 1000) * fps);
	const rel = (at?: number | null, fallback = 0) => (typeof at === 'number' ? Math.round((at - from) * fps) : fallback);
	// progress of an item that enters at `at` (seconds), default brand item duration
	const enter = (at?: number | null, fallback = 0, dur = brand.motion.itemInMs) => eo(frame, rel(at, fallback), rel(at, fallback) + ms(dur));
	return {frame, fps, ms, rel, enter, dur: Math.round((to - from) * fps)};
};
