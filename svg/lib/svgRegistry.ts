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
  private static MAX_ENTRIES = 2000;
  private static keys: string[] = [];

  static register(query: string, provider: SvgProvider, data: PreprocessedSvg) {
    const key = `${provider}:${query}`;

    if (this.assets.has(key)) {
        this.keys = this.keys.filter(k => k !== key);
    } else if (this.assets.size >= this.MAX_ENTRIES) {
        const oldest = this.keys.shift();
        if (oldest) this.assets.delete(oldest);
    }

    this.assets.set(key, data);
    this.keys.push(key);
  }

  static get(query: string, provider: SvgProvider): PreprocessedSvg | undefined {
    const key = `${provider}:${query}`;
    const data = this.assets.get(key);

    if (data) {
        // LRU: Refresh order on access
        this.keys = this.keys.filter(k => k !== key);
        this.keys.push(key);
    }

    return data;
  }

  static clear() {
    this.assets.clear();
    this.keys = [];
  }

  static has(query: string, provider: SvgProvider): boolean {
    return this.assets.has(`${provider}:${query}`);
  }

  /**
   * Bulk load preprocessed assets into the registry.
   * Useful for transferring assets from a preloader to a static render environment.
   */
  static load(data: Record<string, PreprocessedSvg>) {
    Object.entries(data).forEach(([key, value]) => {
      this.assets.set(key, value);
    });
  }

  /**
   * Export all currently registered assets.
   */
  static export(): Record<string, PreprocessedSvg> {
    const data: Record<string, PreprocessedSvg> = {};
    this.assets.forEach((value, key) => {
      data[key] = value;
    });
    return data;
  }
}
