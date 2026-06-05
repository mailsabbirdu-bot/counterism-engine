import os
import json
import requests
import time
from shapely.geometry import shape, mapping
import geopandas as gpd

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
CACHE_DIR = "public/maps/cache"

def fetch_boundary(name):
    filename = os.path.join(CACHE_DIR, f"{name.lower()}.geojson")
    if os.path.exists(filename):
        print(f"✅ {name} already cached.")
        return filename

    print(f"📡 Fetching boundary for: {name}...")
    query = f"""
    [out:json];
    relation["name"="{name}"]["boundary"="administrative"];
    out geom;
    """

    try:
        response = requests.post(OVERPASS_URL, data={'data': query})
        data = response.json()

        if not data.get('elements'):
            # Try without boundary=administrative for smaller areas
            query = f'[out:json];relation["name"="{name}"];out geom;'
            response = requests.post(OVERPASS_URL, data={'data': query})
            data = response.json()

        if not data.get('elements'):
            print(f"⚠️ No data found for {name}")
            return None

        # Convert Overpass OSM JSON to GeoJSON
        # We take the first element for simplicity
        element = data['elements'][0]

        # Simple conversion - in a real tool, we'd use osm2geojson
        # But for boundaries, we can construct the polygon from members
        features = []
        for member in element.get('members', []):
            if member['type'] == 'way' and 'geometry' in member:
                coords = [[p['lon'], p['lat']] for p in member['geometry']]
                features.append({
                    "type": "Feature",
                    "properties": {"name": name},
                    "geometry": {"type": "LineString", "coordinates": coords}
                })

        geojson = {
            "type": "FeatureCollection",
            "features": features
        }

        with open(filename, 'w') as f:
            json.dump(geojson, f)

        print(f"✅ Saved {name} to {filename}")
        return filename
    except Exception as e:
        print(f"❌ Error fetching {name}: {e}")
        return None

def detect_neighbors(names):
    # This is a stub for the logic
    # In a full implementation, we'd load the polygons and check for touches
    # Using geopandas is recommended
    pass

if __name__ == "__main__":
    areas = ["Bangladesh", "Dhaka", "Gulshan", "Banani", "Mohakhali"]
    for area in areas:
        fetch_boundary(area)
        time.sleep(1) # Be nice to Overpass
