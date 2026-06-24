import { SvgProvider } from '../types';

export class SvgProviderService {
  private static FETCH_TIMEOUT = 5000;
  private static MAX_RETRIES = 2;

  /**
   * Fetch SVG data from public APIs based on provider and query.
   */
  static async fetchSvg(query: string, provider: SvgProvider): Promise<string> {
    const cleanQuery = query.trim().toLowerCase();

    // Primary URL based on provider
    let primaryUrl = '';
    switch (provider) {
      case 'lucide':
        // Lucide on Iconify is more robust for aliases
        primaryUrl = `https://api.iconify.design/lucide/${cleanQuery}.svg`;
        break;
      case 'tabler':
        primaryUrl = `https://api.iconify.design/tabler/${cleanQuery}.svg`;
        break;
      case 'iconify':
      default:
        const iconName = cleanQuery.includes(':') ? cleanQuery : `mdi:${cleanQuery}`;
        primaryUrl = `https://api.iconify.design/${iconName.replace(':', '/')}.svg`;
        break;
    }

    try {
        return await this.fetchWithRetry(primaryUrl);
    } catch (e) {
        // FALLBACK: Try standard MDI via Iconify if specific provider fails
        console.warn(`Primary fetch failed for ${cleanQuery}, trying fallback...`);
        const fallbackUrl = `https://api.iconify.design/mdi/${cleanQuery}.svg`;
        return this.fetchWithRetry(fallbackUrl);
    }
  }

  private static async fetchWithRetry(url: string, attempt: number = 0): Promise<string> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.FETCH_TIMEOUT);

      const response = await fetch(url, { signal: controller.signal });
      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP Error: ${response.status}`);
      }

      const svgText = await response.text();

      if (!svgText.includes('<svg')) {
        throw new Error('Invalid SVG content received');
      }

      return svgText;
    } catch (error) {
      if (attempt < this.MAX_RETRIES) {
        return this.fetchWithRetry(url, attempt + 1);
      }
      throw error;
    }
  }
}
