import { SvgScene, SvgProvider, StorytellingElement } from '../types';
import { SvgProviderService } from './SvgProviderService';
import { SvgRegistry } from '../lib/svgRegistry';
import { COMPOSITIONS } from '../lib/compositionLibrary';
import { staticFile } from 'remotion';

/**
 * SVG Asset Preloader
 * Scans scene data and populates the registry for zero-runtime fetching.
 * In production/offline mode, it loads from public/svg-cache/
 */
export class SvgAssetPreloader {
  static async preloadScene(scene: SvgScene) {
    const queries = new Set<{ query: string; provider: SvgProvider }>();
    const sceneProvider = scene.sceneIconTheme || 'lucide';

    // 1. Scan elements
    scene.elements.forEach(el => this.scanElement(el, sceneProvider, queries));

    // 2. Load and process
    const parser = new DOMParser();
    const promises = Array.from(queries).map(async ({ query, provider }) => {
      try {
        // Try local fetch first (via Remotion's public static file system)
        const safeName = `${provider}-${query.replace(/[^a-z0-9]/gi, '_')}.svg`;
        const localUrl = staticFile(`svg-cache/${safeName}`);

        let markup: string;
        try {
            const resp = await fetch(localUrl);
            if (!resp.ok) throw new Error('Local asset not found');
            markup = await resp.text();
        } catch (e) {
            // FALLBACK: Runtime fetch (only if pre-render script was skipped)
            console.warn(`Asset ${query} not found in local cache, falling back to network...`);
            markup = await SvgProviderService.fetchSvg(query, provider);
        }

        const doc = parser.parseFromString(markup, 'image/svg+xml');
        const svg = doc.querySelector('svg');

        if (!svg) throw new Error('Invalid SVG');

        let totalLength = 0;
        const paths = svg.querySelectorAll('path, rect, circle, ellipse, line, polyline, polygon');
        paths.forEach((p: any) => {
            if (p.getTotalLength) {
                try { totalLength = Math.max(totalLength, p.getTotalLength()); } catch(e) {}
            }
        });

        SvgRegistry.register(query, provider, {
          markup,
          pathLength: totalLength || 5000
        });
      } catch (e) {
        console.error(`Failed to preload SVG: ${query}`, e);
      }
    });

    await Promise.all(promises);
  }

  private static scanElement(el: StorytellingElement, defaultProvider: SvgProvider, queries: Set<{ query: string; provider: SvgProvider }>) {
    if (el.type === 'svg') {
      queries.add({ query: el.query, provider: el.provider || defaultProvider });
    } else if (el.type === 'hub_network') {
      queries.add({ query: el.centerSvg, provider: el.provider || defaultProvider });
      el.nodes.forEach(q => queries.add({ query: q, provider: el.provider || defaultProvider }));
    } else if (el.type === 'flow_diagram' || el.type === 'process') {
      el.steps.forEach(q => queries.add({ query: q, provider: defaultProvider }));
    } else if (el.type === 'kpi' && el.icon) {
      queries.add({ query: el.icon, provider: defaultProvider });
    } else if (el.type === 'composition') {
        const comp = COMPOSITIONS[el.compositionType];
        if (comp) {
            comp.elements.forEach(sub => queries.add({ query: sub.query, provider: sub.provider || defaultProvider }));
        }
    }
  }
}
