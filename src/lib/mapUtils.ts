import { staticFile } from 'remotion';
import { resolveAsset } from './resolveAsset';

const DRIVE_MAPS_DIR = '/content/drive/MyDrive/Counterism_Studio_V4/maps';
const LOCAL_MAPS_DIR = './public/maps';

export const getMapDataPath = (name: string) => {
    const fileName = `${name.toLowerCase().replace(/[^a-z0-9]/g, '_')}.json`;
    return {
        drive: `${DRIVE_MAPS_DIR}/${fileName}`,
        local: `${LOCAL_MAPS_DIR}/${fileName}`,
        public: resolveAsset(`maps/${fileName}`)
    };
};

/**
 * Fetches GeoJSON boundaries for a query.
 * Priorities: Local Cache -> Nominatim API
 */
/**
 * Fetches neighboring administrative areas for a given focus result.
 */
export const fetchNeighbors = async (focusResult: any): Promise<any[]> => {
    if (!focusResult || !focusResult.features?.[0]) return [];

    const props = focusResult.features[0].properties;
    const lat = props.lat || (focusResult.features[0].geometry.type === 'Point'
        ? focusResult.features[0].geometry.coordinates[1]
        : (focusResult.features[0].bbox ? (focusResult.features[0].bbox[1] + focusResult.features[0].bbox[3]) / 2 : 23.8));

    const lon = props.lon || (focusResult.features[0].geometry.type === 'Point'
        ? focusResult.features[0].geometry.coordinates[0]
        : (focusResult.features[0].bbox ? (focusResult.features[0].bbox[0] + focusResult.features[0].bbox[2]) / 2 : 90.4));

    console.log(`[MapUtils] Fetching neighbors for ${props.name} at ${lat}, ${lon}`);

    // Search for nearby administrative areas of similar rank
    const searchUrl = `https://nominatim.openstreetmap.org/search?q=administrative+boundary+near+${lat},${lon}&format=json&addressdetails=1&polygon_geojson=1&limit=8`;

    try {
        const response = await fetch(searchUrl, {
            headers: { 'User-Agent': 'Counterism-Studio-V4/1.0' }
        });
        const results = await response.json();

        return results.map((r: any) => ({
            type: 'Feature',
            properties: {
                name: r.display_name.split(',')[0],
                name_bn: r.address?.city_district || r.address?.city || r.address?.state || r.name
            },
            geometry: r.geojson
        }));
    } catch (e) {
        console.error("[MapUtils] Neighbor fetch failed", e);
        return [];
    }
};

export const fetchBoundary = async (query: string): Promise<any> => {
    console.log(`[MapUtils] Fetching boundary for: ${query}`);

    // Standardized sanitization for cache lookups
    const sanitized = query.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');

    // We try multiple variations to be robust against legacy naming
    const cacheFiles = [
        `${sanitized}.geojson`,
        `${query.toLowerCase().replace(/ /g, '_')}.geojson`,
        `${query.toLowerCase()}.geojson`
    ];

    for (const fileName of cacheFiles) {
        const cachedPath = resolveAsset(`maps/cache/${fileName}`);
        try {
            const cachedRes = await fetch(cachedPath);
            if (cachedRes.ok) {
                const data = await cachedRes.json();
                console.log(`[MapUtils] Cache hit: ${fileName}`);
                return data;
            }
        } catch (e) {
            // Ignore fetch errors for cache misses
        }
    }

    // Fallback to external API
    console.log(`[MapUtils] Cache miss for: ${query}. Fetching from Nominatim...`);
    const searchUrl = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&polygon_geojson=1&limit=1`;

    try {
        const response = await fetch(searchUrl, {
            headers: { 'User-Agent': 'Counterism-Studio-V4/1.0' }
        });
        const results = await response.json();

        if (!results || results.length === 0) {
            throw new Error(`No results found for ${query}`);
        }

        const result = results[0];
        if (result.geojson) {
            return {
                type: 'FeatureCollection',
                features: [{
                    type: 'Feature',
                    properties: {
                        name: result.display_name,
                        name_bn: result.address?.city_district || result.address?.city || result.address?.state || result.name,
                        osm_id: result.osm_id,
                        osm_type: result.osm_type,
                        lat: result.lat,
                        lon: result.lon,
                        bbox: result.boundingbox ? [
                            parseFloat(result.boundingbox[2]), // minLon
                            parseFloat(result.boundingbox[0]), // minLat
                            parseFloat(result.boundingbox[3]), // maxLon
                            parseFloat(result.boundingbox[1])  // maxLat
                        ] : null
                    },
                    geometry: result.geojson
                }]
            };
        }
        throw new Error(`No GeoJSON found for ${query}`);
    } catch (error) {
        console.error(`[MapUtils] Error fetching boundary:`, error);
        throw error;
    }
};

export const getBanglaName = (properties: any): string => {
    if (!properties) return '';
    return properties.name_bn || properties['name:bn'] || properties.name || '';
};
