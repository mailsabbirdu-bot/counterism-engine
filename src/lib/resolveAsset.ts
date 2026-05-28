import { staticFile } from 'remotion';

/**
 * Resolves an asset path using staticFile() and ensures it doesn't have
 * redundant /public prefixes that cause 404s in some environments.
 */
export const resolveAsset = (path: string): string => {
  if (!path) return '';

  // If it's already an absolute URL, return as is
  if (path.startsWith('http')) return path;

  const url = staticFile(path);

  // In some environments (like Colab), staticFile might prepend /public/
  // but the server expects it relative to the public root.
  if (url.startsWith('/public/')) {
    return url.replace('/public/', '/');
  }

  return url;
};
