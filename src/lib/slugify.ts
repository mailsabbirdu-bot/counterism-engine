/**
 * Creates a Remotion-safe composition ID.
 * Remotion allows: a-z, A-Z, 0-9, CJK characters and -
 * This utility converts any string into a valid ASCII-safe slug with fallback.
 */
export const slugify = (text: string, fallback: string = 'scene'): string => {
  if (!text) return fallback;

  const slug = text
    .toString()
    .normalize('NFD')                   // split accented characters into their base characters and diacritical marks
    .replace(/[\u0300-\u036f]/g, '')    // remove all the accents, which happen to be all in the \u03xx UNICODE block.
    .trim()                             // trim leading or trailing whitespace
    .toLowerCase()                      // convert to lowercase
    .replace(/[^a-z0-9 -]/g, '')        // remove non-alphanumeric characters (except spaces and hyphens)
    .replace(/\s+/g, '-')               // replace spaces with hyphens
    .replace(/-+/g, '-')               // remove consecutive hyphens
    .replace(/^-+/, '')                 // remove leading hyphens
    .replace(/-+$/, '');                // remove trailing hyphens

  return slug || fallback;
};

/**
 * Returns a Remotion-compliant ID, preserving CJK characters but cleaning everything else.
 */
export const remotionSafeId = (id: string, index: number = 0): string => {
    if (!id) return `scene-${index + 1}`;

    const cleaned = id
        .replace(/_/g, '-')
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[^a-zA-Z0-9-]/g, (char: string) => {
            const code = char.charCodeAt(0);
            if (
                (code >= 0x4e00 && code <= 0x9fff) ||
                (code >= 0x3400 && code <= 0x4dbf) ||
                (code >= 0x3040 && code <= 0x309f) ||
                (code >= 0x30a0 && code <= 0x30ff) ||
                (code >= 0xac00 && code <= 0xd7af)
            ) return char;
            return '-';
        })
        .replace(/-+/g, '-')
        .replace(/^-|-$/g, '');

    return cleaned || `scene-${index + 1}`;
};
