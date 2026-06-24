import { SvgScene, SvgProvider, StorytellingElement } from '../types';
import { SvgProviderService } from './SvgProviderService';
import { SvgRegistry } from '../lib/svgRegistry';
import { COMPOSITIONS } from '../lib/compositionLibrary';

/**
 * SVG Asset Preloader
 * Scans scene data and downloads/processes all required SVGs before rendering.
 * MUST be called during the setup/pre-render phase.
 */
export class SvgAssetPreloader {
  static async preloadScene(scene: SvgScene) {
    const queries = new Set<{ query: string; provider: SvgProvider }>();
    const sceneProvider = scene.sceneIconTheme || 'lucide';

    // 1. Scan elements
    scene.elements.forEach(el => this.scanElement(el, sceneProvider, queries));

    // 2. Scan hub networks (center and outer nodes)
    scene.elements.forEach(el => {
        if (el.type === 'hub_network') {
            queries.add({ query: el.centerSvg, provider: el.provider || sceneProvider });
            el.nodes.forEach(q => queries.add({ query: queryToKey(q), provider: el.provider || sceneProvider }));
        }
    });

    function queryToKey(q: string) { return q; }

    // 3. Download and process
    const parser = new DOMParser();
    const promises = Array.from(queries).map(async ({ query, provider }) => {
      try {
        const markup = await SvgProviderService.fetchSvg(query, provider);
        const doc = parser.parseFromString(markup, 'image/svg+xml');
        const svg = doc.querySelector('svg');

        if (!svg) throw new Error('Invalid SVG');

        // Extract total path length (approximation or measurement)
        let totalLength = 0;
        const paths = svg.querySelectorAll('path, rect, circle, ellipse, line, polyline, polygon');
        paths.forEach((p: any) => {
            if (p.getTotalLength) {
                totalLength = Math.max(totalLength, p.getTotalLength());
            } else {
                const bbox = p.getBBox();
                totalLength = Math.max(totalLength, (bbox.width + bbox.height) * 2);
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
