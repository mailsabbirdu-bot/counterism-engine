import { random } from 'remotion';

/**
 * Generate a unique ID for SVG markers, gradients, etc.
 * Prevents DOM collisions when many instances are rendered.
 */
export const generateSvgId = (base: string, seed: any) => {
    // We use Remotion's random() for determinism
    const unique = Math.floor(random(seed) * 1000000);
    return `${base}-${unique}`;
};
