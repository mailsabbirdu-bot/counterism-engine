import fs from 'fs';
import path from 'path';
import { SvgProvider } from '../types';

/**
 * Local SVG File Store
 * Manages caching of SVGs in the public/ folder for offline rendering.
 */
export class SvgFileStore {
    private static CACHE_DIR = 'public/svg-cache';

    static ensureCacheDir() {
        if (!fs.existsSync(this.CACHE_DIR)) {
            fs.mkdirSync(this.CACHE_DIR, { recursive: true });
        }
    }

    static getLocalPath(query: string, provider: SvgProvider): string {
        const safeName = `${provider}-${query.replace(/[^a-z0-9]/gi, '_')}.svg`;
        return path.join(this.CACHE_DIR, safeName);
    }

    static exists(query: string, provider: SvgProvider): boolean {
        return fs.existsSync(this.getLocalPath(query, provider));
    }

    static save(query: string, provider: SvgProvider, markup: string) {
        this.ensureCacheDir();
        fs.writeFileSync(this.getLocalPath(query, provider), markup);
    }

    static load(query: string, provider: SvgProvider): string | null {
        if (this.exists(query, provider)) {
            return fs.readFileSync(this.getLocalPath(query, provider), 'utf8');
        }
        return null;
    }
}
