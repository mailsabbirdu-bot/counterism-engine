import { ENGINE_CONSTANTS } from './constants';

export type AnimationStyles = React.CSSProperties;

export interface AnimationParams {
    relativeFrame: number;
    spr: number;
    baseScale: number;
    baseOpacity: number;
}

export const animationRegistry: Record<string, (params: AnimationParams) => AnimationStyles> = {
    fade: ({ spr, baseOpacity }) => ({
        opacity: spr * baseOpacity
    }),
    scale: ({ spr, baseScale, baseOpacity }) => ({
        opacity: spr * baseOpacity,
        transform: `scale(${spr * baseScale})`
    }),
    pop: ({ spr, baseScale, baseOpacity }) => ({
        opacity: spr * baseOpacity,
        transform: `scale(${spr * 1.1 * baseScale})`
    }),
    rotate: ({ spr, baseScale, baseOpacity }) => ({
        opacity: spr * baseOpacity,
        transform: `rotate(${(spr * 360) % 360}deg) scale(${spr * baseScale})`
    }),
    slideUp: ({ spr, baseScale, baseOpacity }) => ({
        opacity: spr * baseOpacity,
        transform: `translateY(${(1 - spr) * 100}px) scale(${baseScale})`
    }),
    slideDown: ({ spr, baseScale, baseOpacity }) => ({
        opacity: spr * baseOpacity,
        transform: `translateY(${(spr - 1) * 100}px) scale(${baseScale})`
    }),
    pulse: ({ relativeFrame, spr, baseScale, baseOpacity }) => {
        const pulse = 1 + Math.sin(relativeFrame / 10) * 0.05;
        return {
            opacity: baseOpacity,
            transform: `scale(${spr * baseScale * pulse})`
        };
    },
    float: ({ relativeFrame, spr, baseScale, baseOpacity }) => {
        const floatY = Math.sin(relativeFrame / 20) * 20;
        return {
            opacity: spr * baseOpacity,
            transform: `translateY(${floatY}px) scale(${spr * baseScale})`
        };
    },
    orbit: ({ relativeFrame, spr, baseScale, baseOpacity }) => {
        const orbitX = Math.cos(relativeFrame / 30) * 50;
        const orbitY = Math.sin(relativeFrame / 30) * 50;
        return {
            opacity: spr * baseOpacity,
            transform: `translate(${orbitX}px, ${orbitY}px) scale(${spr * baseScale})`
        };
    },
    reveal: ({ spr, baseScale }) => ({
        opacity: 1,
        clipPath: `inset(0 ${100 - spr * 100}% 0 0)`,
        transform: `scale(${baseScale})`
    }),
    draw: ({ baseScale }) => ({
        opacity: 1,
        transform: `scale(${baseScale})`
    }),
    trace: ({ baseScale }) => ({
        opacity: 1,
        transform: `scale(${baseScale})`
    }),
    glowPulse: ({ baseScale }) => ({
        opacity: 1,
        transform: `scale(${baseScale})`
    })
};

export const getAnimationStyles = (
    animation: string,
    params: AnimationParams
): AnimationStyles => {
    const animator = animationRegistry[animation] || animationRegistry.fade;
    return animator(params);
};
