import { ENGINE_CONSTANTS } from './constants';

/**
 * Shared Layout Utilities
 */

/**
 * Radial Layout Algorithm
 * Used for orbit, radial, and cluster layouts.
 */
export const calculateRadialPosition = (
    index: number,
    total: number,
    baseX: number,
    baseY: number,
    radius: number,
    angleOffset: number = 0
) => {
    if (total <= 0) return { x: baseX, y: baseY };
    // HARDENING (P2-5): Shared radial layout logic.
    // This now serves orbit, radial, and cluster.
    const angle = (index / total) * Math.PI * 2 + angleOffset;
    return {
        x: baseX + Math.cos(angle) * radius,
        y: baseY + Math.sin(angle) * radius
    };
};

/**
 * Linear Layout Algorithm
 * Used for horizontal and vertical layouts.
 */
export const calculateLinearPosition = (
    index: number,
    total: number,
    baseX: number,
    baseY: number,
    spacing: number,
    direction: 'horizontal' | 'vertical'
) => {
    const offset = (index - (total - 1) / 2) * spacing;
    return {
        x: direction === 'horizontal' ? baseX + offset : baseX,
        y: direction === 'vertical' ? baseY + offset : baseY
    };
};

/**
 * Grid Layout Algorithm
 */
export const calculateGridPosition = (
    index: number,
    total: number,
    baseX: number,
    baseY: number,
    spacing: number
) => {
    const cols = Math.ceil(Math.sqrt(total));
    const rows = Math.ceil(total / cols);
    const row = Math.floor(index / cols);
    const col = index % cols;

    return {
        x: baseX + (col - (cols - 1) / 2) * spacing,
        y: baseY + (row - (rows - 1) / 2) * spacing
    };
};
