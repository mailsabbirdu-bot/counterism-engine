import { staticFile } from 'remotion';

/**
 * Resolves an asset path using staticFile() and ensures it is correctly
 * formatted for the environment.
 */
export const resolveAsset = (path: string): string => {
  if (!path) return '';

  // If it's already an absolute URL, return as is
  if (path.startsWith('http')) return path;

  // Ensure we don't have leading slashes that might cause double-prefixing
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;
  const url = staticFile(cleanPath);

  console.log(`[resolveAsset] Original: ${path} -> Clean: ${cleanPath} -> Final URL: ${url}`);

  return url;
};
