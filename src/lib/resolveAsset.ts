import { staticFile } from 'remotion';

/**
 * Resolves an asset path.
 * Standard Remotion behavior is usually sufficient, but we add
 * defensive logic for various environments.
 */
export const resolveAsset = (path: string): string => {
  if (!path) return '';
  if (path.startsWith('http')) return path;

  // staticFile handles the /public prefixing and base URL resolution
  return staticFile(path.startsWith('/') ? path.slice(1) : path);
};
