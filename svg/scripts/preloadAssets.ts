import fs from 'fs';
import path from 'path';
import { SvgProviderService } from '../services/SvgProviderService';
import { SvgFileStore } from '../services/SvgFileStore';
import { SvgScene, SvgProvider, StorytellingElement } from '../types';
import { COMPOSITIONS } from '../lib/compositionLibrary';

/**
 * Pre-render Asset Downloader
 * Scans a Remotion template and downloads all SVGs to local storage.
 */
async function preloadAll() {
    const templatePath = process.argv.slice(2)[0] || 'remotion_render.json';
    if (!fs.existsSync(templatePath)) {
        console.error(`❌ Template not found: ${templatePath}`);
        return;
    }

    const template = JSON.parse(fs.readFileSync(templatePath, 'utf8'));
    const queries = new Set<string>(); // "provider:query"

    template.scenes.forEach((scene: any) => {
        const sceneProvider = scene.sceneIconTheme || 'lucide';
        (scene.elements || []).forEach((el: any) => scanElement(el, sceneProvider, queries));
    });

    console.log(`🔍 Found ${queries.size} unique SVGs to preload...`);

    for (const entry of queries) {
        const [provider, query] = entry.split(':');
        if (SvgFileStore.exists(query, provider as SvgProvider)) {
            console.log(`  ✅ ${entry} already in local store.`);
            continue;
        }

        try {
            console.log(`  📡 Downloading ${entry}...`);
            const markup = await SvgProviderService.fetchSvg(query, provider as SvgProvider);
            SvgFileStore.save(query, provider as SvgProvider, markup);
            console.log(`  ✨ Saved ${entry} locally.`);
        } catch (e) {
            console.error(`  ❌ Failed to download ${entry}:`, e);
        }
    }
}

function scanElement(el: any, defaultProvider: SvgProvider, queries: Set<string>) {
    if (el.type === 'svg') {
      queries.add(`${el.provider || defaultProvider}:${el.query}`);
    } else if (el.type === 'hub_network') {
      queries.add(`${el.provider || defaultProvider}:${el.centerSvg}`);
      (el.nodes || []).forEach((q: string) => queries.add(`${el.provider || defaultProvider}:${q}`));
    } else if (el.type === 'flow_diagram' || el.type === 'process') {
      (el.steps || []).forEach((q: string) => queries.add(`${defaultProvider}:${q}`));
    } else if (el.type === 'kpi' && el.icon) {
      queries.add(`${defaultProvider}:${el.icon}`);
    } else if (el.type === 'composition') {
        const comp = COMPOSITIONS[el.compositionType];
        if (comp) {
            comp.elements.forEach((sub: any) => queries.add(`${sub.provider || defaultProvider}:${sub.query}`));
        }
    }
}

preloadAll().then(() => console.log("🏁 Preloading complete."));
