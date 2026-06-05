import os
import json
import osmnx as ox
import geopandas as gpd
import pandas as pd
from shapely.geometry import mapping
import time

CACHE_DIR = "public/maps/cache"
METADATA_FILE = "public/maps/metadata.json"

os.makedirs(CACHE_DIR, exist_ok=True)

def fetch_area_data(names):
    print(f"📡 Fetching and analyzing: {names}")

    # Fetch boundaries using OSMnx (very robust)
    try:
        # We fetch them one by one to handle potential failures
        gdfs = []
        for name in names:
            try:
                print(f"  🔍 Geocoding {name}...")
                gdf = ox.geocode_to_gdf(name)
                if not gdf.empty:
                    gdf['search_name'] = name
                    gdfs.append(gdf)
                else:
                    print(f"  ⚠️ No geometry found for {name}")
            except Exception as e:
                print(f"  ❌ Error fetching {name}: {e}")
            time.sleep(1)

        if not gdfs:
            print("❌ No data fetched.")
            return

        master_gdf = pd.concat(gdfs).reset_index(drop=True)

        # Save individual GeoJSONs
        for i, row in master_gdf.iterrows():
            name = row['search_name']
            filename = os.path.join(CACHE_DIR, f"{name.lower().replace(' ', '_')}.geojson")

            # Create a single feature GeoJSON
            feature_collection = {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {
                        "name": name,
                        "display_name": row.get('display_name', name)
                    },
                    "geometry": mapping(row.geometry)
                }]
            }

            with open(filename, 'w') as f:
                json.dump(feature_collection, f)
            print(f"  ✅ Saved {name} to {filename}")

        # Neighbor Discovery & Metadata
        metadata = {}
        for i, row in master_gdf.iterrows():
            name = row['search_name']

            # Find neighbors (touching polygons)
            neighbors = []
            for j, other_row in master_gdf.iterrows():
                if i != j:
                    if row.geometry.touches(other_row.geometry) or row.geometry.intersects(other_row.geometry):
                        neighbors.append(other_row['search_name'])

            bounds = row.geometry.bounds # (minx, miny, maxx, maxy)

            metadata[name] = {
                "id": name.lower().replace(' ', '_'),
                "display_name": row.get('display_name', name),
                "centroid": [row.geometry.centroid.x, row.geometry.centroid.y],
                "bounds": [bounds[0], bounds[1], bounds[2], bounds[3]],
                "neighbors": neighbors
            }

        with open(METADATA_FILE, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"🎉 Architecture Complete! Metadata saved to {METADATA_FILE}")

    except Exception as e:
        print(f"💥 Fatal Error in Pipeline: {e}")

if __name__ == "__main__":
    # The user's specific example
    targets = [
        "Gulshan, Dhaka, Bangladesh",
        "Banani, Dhaka, Bangladesh",
        "Mohakhali, Dhaka, Bangladesh",
        "Badda, Dhaka, Bangladesh",
        "Tejgaon, Dhaka, Bangladesh",
        "Dhaka, Bangladesh"
    ]
    fetch_area_data(targets)
