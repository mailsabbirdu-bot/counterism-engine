import { SvgScene, SvgProvider, StorytellingElement } from '../types';
import { SvgProviderService } from './SvgProviderService';
import { SvgRegistry } from '../lib/svgRegistry';
import { COMPOSITIONS } from '../lib/compositionLibrary';
import { BUNDLED_ICONS } from '../lib/bundledIcons';

/**
 * SVG Asset Preloader
 * Scans scene data and downloads/processes all required SVGs before rendering.
 * MUST be called during the setup/pre-render phase.
 */
export class SvgAssetPreloader {
  static async preloadScene(scene: SvgScene) {
    const queries = new Set<{ query: string; provider: SvgProvider }>();
    const sceneProvider = scene.sceneIconTheme || 'lucide';
    const elements = scene.elements || scene.overlays || [];

    // 1. Scan elements
    elements.forEach(el => this.scanElement(el, sceneProvider, queries));

    // 2. Scan hub networks (center and outer nodes)
    elements.forEach(el => {
        if (el.type === 'hub_network') {
            queries.add({ query: el.centerSvg, provider: el.provider || sceneProvider });
            el.nodes.forEach(q => queries.add({ query: queryToKey(q), provider: el.provider || sceneProvider }));
        }
    });

    function queryToKey(q: string) { return q; }

    // 3. Download and process
    // Note: DOMParser is used here in the preprocessing stage (pre-render).
    // This is acceptable as long as it's not in the main render loop.
    const parser = typeof DOMParser !== 'undefined' ? new DOMParser() : null;

    const promises = Array.from(queries).map(async ({ query, provider }) => {
      try {
        // LOCAL FIRST RESOLUTION
        const localMarkup = BUNDLED_ICONS[query.toLowerCase()];
        const markup = localMarkup || await SvgProviderService.fetchSvg(query, provider);

        let totalLength = 5000; // Default fallback

        if (parser) {
            const doc = parser.parseFromString(markup, 'image/svg+xml');
            const svg = doc.querySelector('svg');

            if (svg) {
                // Extract total path length (approximation or measurement)
                let maxPathLength = 0;
                const paths = svg.querySelectorAll('path, rect, circle, ellipse, line, polyline, polygon');
                paths.forEach((p: any) => {
                    if (p.getTotalLength) {
                        maxPathLength = Math.max(maxPathLength, p.getTotalLength());
                    } else {
                        // Fallback measurement if getTotalLength is not available
                        const bbox = p.getBBox ? p.getBBox() : { width: 100, height: 100 };
                        maxPathLength = Math.max(maxPathLength, (bbox.width + bbox.height) * 2);
                    }
                });
                totalLength = maxPathLength || 5000;
            }
        }

        SvgRegistry.register(query, provider, {
          markup,
          pathLength: totalLength
        });
      } catch (e) {
        console.error(`Failed to preload SVG: ${query}`, e);
      }
    });

    await Promise.all(promises);
  }

  private static scanElement(el: StorytellingElement, defaultProvider: SvgProvider, queries: Set<{ query: string; provider: SvgProvider }>) {
    if (el.type === 'svg' && el.query) {
      queries.add({ query: el.query, provider: el.provider || defaultProvider });
    } else if (el.type === 'hub_network' && el.centerSvg) {
      queries.add({ query: el.centerSvg, provider: el.provider || defaultProvider });
      if (el.nodes) el.nodes.forEach(q => queries.add({ query: q, provider: el.provider || defaultProvider }));
    } else if ((el.type === 'flow_diagram' || el.type === 'process') && el.steps) {
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
