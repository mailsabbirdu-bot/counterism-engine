import { staticFile } from 'remotion';

/**
 * Resolves an asset path using staticFile() and ensures it is correctly
 * formatted for the environment.
 */
export const resolveAsset = (path: string): string => {
  if (!path) return '';

  // If it's already an absolute URL, return as is
  if (path.startsWith('http')) return path;

  // Ensure we don't have leading slashes for staticFile
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;
  let url = staticFile(cleanPath);

  // HEADLESS/COLAB FIX:
  // Remotion's staticFile often returns "/public/..." in certain environments.
  // The asset server usually serves from the root.
  if (url.startsWith('/public/')) {
    url = url.replace('/public/', '/');
  } else if (url.includes('/public/')) {
    // Handle cases like "http://localhost:3000/public/..."
    url = url.replace('/public/', '/');
  }

  return url;
};
