import os
import json
import requests
import time
import geopandas as gpd
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
import pandas as pd

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
CACHE_DIR = "public/maps/cache"
METADATA_FILE = "public/maps/metadata.json"

os.makedirs(CACHE_DIR, exist_ok=True)

def fetch_osm_relation(name):
    query = f"""
    [out:json];
    relation["name"="{name}"];
    out geom;
    """
    try:
        response = requests.post(OVERPASS_URL, data={'data': query}, timeout=30)
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching {name}: {e}")
        return None

def process_area(name):
    geojson_path = os.path.join(CACHE_DIR, f"{name.lower()}.geojson")
    if os.path.exists(geojson_path):
        return gpd.read_file(geojson_path)

    print(f"📡 Fetching boundary for: {name}...")
    data = fetch_osm_relation(name)
    if not data or not data.get('elements'):
        print(f"⚠️ No elements found for {name}")
        return None

    element = data['elements'][0]
    features = []

    # Simple reconstruction from OSM geometry
    # In a production environment, we'd use a more robust OSM-to-GeoJSON converter
    for member in element.get('members', []):
        if 'geometry' in member and len(member['geometry']) > 1:
            coords = [[p['lon'], p['lat']] for p in member['geometry']]
            features.append({
                "type": "Feature",
                "properties": {"name": name},
                "geometry": {"type": "LineString", "coordinates": coords}
            })

    if not features:
        return None

    # Save raw lines as GeoJSON
    geojson = {"type": "FeatureCollection", "features": features}
    with open(geojson_path, 'w') as f:
        json.dump(geojson, f)

    return gpd.read_file(geojson_path)

def generate_metadata(area_names):
    metadata = {}
    gdfs = []

    for name in area_names:
        gdf = process_area(name)
        if gdf is not None:
            # Union the lines and try to polygonize
            merged_geom = unary_union(gdf.geometry)
            # If it's a closed ring, we treat it as a polygon for centroid/neighbor logic
            metadata[name] = {
                "centroid": [merged_geom.centroid.x, merged_geom.centroid.y],
                "bounds": merged_geom.bounds, # [minx, miny, maxx, maxy]
                "neighbors": []
            }
            # Keep a master GDF for spatial joins
            gdf_poly = gdf.copy()
            gdf_poly['name'] = name
            gdf_poly.geometry = [merged_geom]
            gdfs.append(gdf_poly)
        time.sleep(1)

    # Neighbor Discovery
    if len(gdfs) > 1:
        master_gdf = pd.concat(gdfs).reset_index(drop=True)
        for i, row in master_gdf.iterrows():
            # Find which other areas touch this one
            touches = master_gdf[master_gdf.geometry.touches(row.geometry)]
            metadata[row['name']]["neighbors"] = touches['name'].tolist()

    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"✅ Metadata saved to {METADATA_FILE}")

if __name__ == "__main__":
    # Example for Dhaka neighborhood analysis
    targets = ["Dhaka", "Gulshan", "Banani", "Mohakhali", "Badda", "Tejgaon"]
    generate_metadata(targets)
