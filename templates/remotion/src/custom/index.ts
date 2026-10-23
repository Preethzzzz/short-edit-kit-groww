// Job-local components and scenes. render.py replaces this file when the job has a custom/ folder:
// custom/<Name>.tsx (default export) -> beat component <Name>; custom/Scene<Name>.tsx -> scene "<name>".
import type React from 'react';

export const CUSTOM: Record<string, React.FC<any>> = {};
export const CUSTOM_SCENES: Record<string, React.FC> = {};
