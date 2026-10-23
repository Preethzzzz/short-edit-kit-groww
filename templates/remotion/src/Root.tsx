import React from 'react';
import {CalculateMetadataFunction, Composition} from 'remotion';
import sample from './sample.json';
import {Short} from './Short';
import type {EditProps} from './types';

// Size, fps and length come from the edit plan passed with --props (edit.json).
const meta: CalculateMetadataFunction<EditProps> = ({props}) => ({
	durationInFrames: Math.max(1, Math.round(props.duration * props.fps)),
	fps: props.fps,
	width: props.width,
	height: props.height,
});

export const RemotionRoot: React.FC = () => (
	<Composition id="Short" component={Short} defaultProps={sample as unknown as EditProps} calculateMetadata={meta} durationInFrames={300} fps={30} width={1080} height={1920} />
);
