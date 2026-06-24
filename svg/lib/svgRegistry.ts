import { SvgProvider } from '../types';

export interface PreprocessedSvg {
  markup: string;
  pathLength: number;
}

/**
 * Global SVG Registry
 * Stores preprocessed SVG data for zero-runtime fetching and parsing.
 */
export class SvgRegistry {
  private static assets: Map<string, PreprocessedSvg> = new Map();

  static register(query: string, provider: SvgProvider, data: PreprocessedSvg) {
    const key = `${provider}:${query}`;
    this.assets.set(key, data);
  }

  static get(query: string, provider: SvgProvider): PreprocessedSvg | undefined {
    const key = `${provider}:${query}`;
    return this.assets.get(key);
  }

  static clear() {
    this.assets.clear();
  }

  static has(query: string, provider: SvgProvider): boolean {
    return this.assets.has(`${provider}:${query}`);
  }
}
