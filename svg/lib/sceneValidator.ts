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

    // 4. Check for Empty Container Elements
    scene.elements.forEach(el => {
        if (el.type === 'hub_network' && el.nodes.length === 0) {
            // This is handled in the component now, but good to validate.
            // errors.push(`Hub Network "${el.id}" has no nodes.`);
        }
        if (el.type === 'process' && el.steps.length === 0) {
            errors.push(`Process Diagram "${el.id}" has no steps.`);
        }
    });

    return errors;
};
