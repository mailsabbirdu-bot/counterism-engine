import { SvgProvider } from '../types';

export class SvgProviderService {
  private static FETCH_TIMEOUT = 5000;
  private static MAX_RETRIES = 2;

  /**
   * Fetch SVG data from public APIs based on provider and query.
   */
  static async fetchSvg(query: string, provider: SvgProvider): Promise<string> {
    let url = '';

    // Normalize query (e.g. house -> mdi:house for iconify if needed)
    const cleanQuery = query.trim().toLowerCase();

    switch (provider) {
      case 'iconify':
        // Iconify supports many sets. Defaulting to mdi if no set prefix provided
        const iconName = cleanQuery.includes(':') ? cleanQuery : `mdi:${cleanQuery}`;
        url = `https://api.iconify.design/${iconName.replace(':', '/')}.svg`;
        break;
      case 'lucide':
        url = `https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/${cleanQuery}.svg`;
        break;
      case 'tabler':
        url = `https://raw.githubusercontent.com/tabler/tabler-icons/master/icons/${cleanQuery}.svg`;
        break;
      default:
        throw new Error(`Unsupported provider: ${provider}`);
    }

    return this.fetchWithRetry(url);
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
        console.warn(`Retrying fetch for ${url} (Attempt ${attempt + 1})...`);
        return this.fetchWithRetry(url, attempt + 1);
      }
      throw error;
    }
  }
}
