/**
 * Creates a Remotion-safe composition ID.
 * Remotion allows: a-z, A-Z, 0-9, CJK characters and -
 */
export const remotionSafeId = (id: string, index: number = 0): string => {
    if (!id) return `scene-${index + 1}`;

    // Stricter slugification to avoid any Remotion validation issues
    // We force ASCII for composition IDs to be absolutely safe across all environments
    const cleaned = id
        .toString()
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "") // Remove accents
        .replace(/[^a-z0-9]/g, '-')     // Force ASCII
        .replace(/-+/g, '-')             // Remove double hyphens
        .replace(/^-+|-+$/g, '');         // Remove leading/trailing hyphens

    return cleaned || `scene-${index + 1}`;
};
