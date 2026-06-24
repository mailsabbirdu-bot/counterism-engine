import { SvgScene, StorytellingElement } from '../types';

/**
 * Scene Validation Utility
 * Checks for logical errors in the scene manifest before rendering.
 */
export const validateScene = (scene: SvgScene): string[] => {
    const errors: string[] = [];
    const elementIds = new Set(scene.elements.map(el => el.id));

    // 1. Check for Duplicate IDs
    if (elementIds.size !== scene.elements.length) {
        errors.push('Duplicate element IDs detected in scene.');
    }

    // 2. Check for Broken Targets (Labels/Callouts)
    scene.elements.forEach(el => {
        if (el.type === 'label' || el.type === 'callout') {
            if (!elementIds.has(el.target) && !el.target.includes('_center')) {
                errors.push(`Element "${el.id}" targets missing ID "${el.target}".`);
            }
        }
    });

    // 3. Check for Missing Providers
    scene.elements.forEach(el => {
        if (el.type === 'svg' && !el.provider && !scene.sceneIconTheme) {
            errors.push(`SVG Element "${el.id}" is missing a provider and no sceneIconTheme is set.`);
        }
    });

    return errors;
};
