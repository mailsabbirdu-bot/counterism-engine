import { SvgProvider } from '../types';
import { SvgProviderService } from './SvgProviderService';

export class SvgCacheService {
  private static cache: Map<string, Promise<string>> = new Map();
  private static MAX_ENTRIES = 1000;
  private static keys: string[] = [];

  static async getSvg(query: string, provider: SvgProvider): Promise<string> {
    const key = `${provider}:${query}`;

    // LRU Implementation (P1-4: Refresh order on access)
    if (this.cache.has(key)) {
      // Move key to end to represent most recently used
      this.keys = this.keys.filter(k => k !== key);
      this.keys.push(key);
      return this.cache.get(key)!;
    }

    // Capacity check before adding new
    if (this.cache.size >= this.MAX_ENTRIES) {
        const oldest = this.keys.shift();
        if (oldest) this.cache.delete(oldest);
    }

    const fetchPromise = SvgProviderService.fetchSvg(query, provider);

    // HARDENING (P1-5: Remove failed promises from cache)
    fetchPromise.catch(() => {
        this.cache.delete(key);
        this.keys = this.keys.filter(k => k !== key);
    });

    this.cache.set(key, fetchPromise);
    this.keys.push(key);

    return fetchPromise;
  }
}
