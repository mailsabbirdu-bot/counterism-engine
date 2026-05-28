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
  let url = staticFile(cleanPath);

  // In some environments (like Colab), staticFile might prepend /public/
  // but the server expects it relative to the public root.
  if (url.startsWith('/public/')) {
    url = url.replace('/public/', '/');
  }

  console.log(`[resolveAsset] Original: ${path} -> Clean: ${cleanPath} -> Final URL: ${url}`);

  return url;
};
