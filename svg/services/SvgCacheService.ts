import { SvgProvider } from '../types';
import { SvgProviderService } from './SvgProviderService';

export class SvgCacheService {
  private static cache: Map<string, Promise<string>> = new Map();
  private static MAX_ENTRIES = 500;
  private static keys: string[] = [];

  static async getSvg(query: string, provider: SvgProvider): Promise<string> {
    const key = `${provider}:${query}`;

    if (this.cache.has(key)) {
      return this.cache.get(key)!;
    }

    // LRU Implementation
    if (this.cache.size >= this.MAX_ENTRIES) {
        const oldest = this.keys.shift();
        if (oldest) this.cache.delete(oldest);
    }

    const fetchPromise = SvgProviderService.fetchSvg(query, provider);
    this.cache.set(key, fetchPromise);
    this.keys.push(key);

    return fetchPromise;
  }
}
