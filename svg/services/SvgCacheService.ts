import { SvgProvider } from '../types';
import { SvgProviderService } from './SvgProviderService';

export class SvgCacheService {
  private static cache: Map<string, Promise<string>> = new Map();

  static getSvg(query: string, provider: SvgProvider): Promise<string> {
    const key = `${provider}:${query}`;
    if (this.cache.has(key)) {
      return this.cache.get(key)!;
    }

    const fetchPromise = SvgProviderService.fetchSvg(query, provider);
    this.cache.set(key, fetchPromise);
    return fetchPromise;
  }
}
