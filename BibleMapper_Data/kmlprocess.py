import json
import xml.etree.ElementTree as ET
import csv
import re
import difflib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
KML_PATH = REPO_ROOT / "all_bible_places.kml"
CSV_PATH = REPO_ROOT / "TopBibleLocations - Sheet1.csv"
OUTPUT_GEOJSON_PATH = REPO_ROOT / "bible_places.geojson"

# Main Anchors (Rank 1)
MAIN_ANCHORS = {
    "egypt", "athens", "babylon", "judea", "judaea",
    "cyprus", "crete", "rome", "asia", "assyria"
}

# Mid Anchors (Rank 2)
MID_ANCHORS = {
    "jerusalem", "samaria", "malta", "corinth", "patmos", 
    "ephesus", "colossae", "lystra", "galatia", "antioch", 
    "damascus", "galilee", "shiloh", "dan", "beersheba", 
    "philistia", "midian", "rameses", "persia", "ninevah",
    "mediterranean sea", "dead sea" 
}

# Center overrides
MANUAL_OVERRIDES = {
    "egypt": [30.0000, 27.0000],          
    "sea of galilee": [35.5800, 32.8000],
    "mediterranean sea": [23.7000, 34.5000], 
    "dead sea": [35.4800, 31.6500],
    "judaea": [35.1000, 31.6500],
    "judea": [35.1000, 31.6500] 
}

# Hierarchy of shapes: We ALWAYS want a Polygon or Line over a Point
GEOM_RANK = {
    "Polygon": 3,
    "LineString": 2,
    "Point": 1
}

def get_full_text(element):
    if element is not None:
        return "".join(element.itertext()).strip()
    return ""

def kml_to_geojson():
    if not KML_PATH.exists() or not CSV_PATH.exists():
        raise FileNotFoundError("Missing KML or CSV file. Check your folder.")

    csv_locations = {}
    
    for anchor in MAIN_ANCHORS:
        csv_locations[anchor] = {"display_name": anchor.title(), "importance": 1}
    for anchor in MID_ANCHORS:
        csv_locations[anchor] = {"display_name": anchor.title(), "importance": 2}
        
    csv_locations["sea of galilee"] = {"display_name": "Sea of Galilee", "importance": 3}

    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0].strip():
                display_name = row[0].strip()
                clean_csv = re.sub(r'[^a-z\s]', '', display_name.lower()).strip()
                
                if clean_csv in MAIN_ANCHORS:
                    rank = 1
                elif clean_csv in MID_ANCHORS:
                    rank = 2
                else:
                    rank = 3 
                
                if clean_csv not in csv_locations:
                    csv_locations[clean_csv] = {
                        "display_name": display_name,
                        "importance": rank 
                    }

    tree = ET.parse(KML_PATH)
    root = tree.getroot()
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}

    unique_names = {}
    matched_csv_keys = set() 

    for placemark in root.findall('.//kml:Placemark', ns):
        name_el = placemark.find('kml:name', ns)
        raw_name = get_full_text(name_el)
        
        if not raw_name:
            continue

        clean_kml = re.sub(r'\(.*?\)', '', raw_name) 
        clean_kml = re.sub(r'[~%]', '', clean_kml)
        clean_kml = re.sub(r'[^a-z\s]', '', clean_kml.lower()).strip()

        matched_csv_key = None
        
        if clean_kml in MANUAL_OVERRIDES and clean_kml in csv_locations:
            matched_csv_key = clean_kml
        else:
            for csv_key in csv_locations.keys():
                if re.search(rf'\b{re.escape(csv_key)}\b', clean_kml):
                    matched_csv_key = csv_key
                    break
                    
            if not matched_csv_key:
                close_matches = difflib.get_close_matches(clean_kml, csv_locations.keys(), n=1, cutoff=0.85)
                if close_matches:
                    matched_csv_key = close_matches[0]

        if not matched_csv_key:
            continue

        desc_el = placemark.find('kml:description', ns)
        desc_text = get_full_text(desc_el)
        mentions = desc_text.count(',') + desc_text.count(';') + 1 if desc_text else 1

        pt_node = placemark.find('.//kml:Point/kml:coordinates', ns)
        line_node = placemark.find('.//kml:LineString/kml:coordinates', ns)
        poly_node = placemark.find('.//kml:Polygon//kml:coordinates', ns)

        geom_type = None
        geom_coords = None
        best_lon, best_lat = None, None

        if pt_node is not None:
            raw = get_full_text(pt_node).split()
            if raw:
                parts = [float(c) for c in raw[0].split(',') if c]
                if len(parts) >= 2:
                    geom_type = "Point"
                    geom_coords = [parts[0], parts[1]]
                    best_lon, best_lat = parts[0], parts[1]
                    
        elif line_node is not None:
            raw = get_full_text(line_node).split()
            coords = []
            for pair in raw:
                parts = [float(c) for c in pair.split(',') if c]
                if len(parts) >= 2:
                    coords.append([parts[0], parts[1]])
            if coords:
                geom_type = "LineString"
                geom_coords = coords
                mid = len(coords) // 2
                best_lon, best_lat = coords[mid][0], coords[mid][1]
                
        elif poly_node is not None:
            raw = get_full_text(poly_node).split()
            coords = []
            lons, lats = [], []
            for pair in raw:
                parts = [float(c) for c in pair.split(',') if c]
                if len(parts) >= 2:
                    coords.append([parts[0], parts[1]])
                    lons.append(parts[0])
                    lats.append(parts[1])
            if coords:
                geom_type = "Polygon"
                geom_coords = [coords] 
                best_lon, best_lat = round((max(lons) + min(lons)) / 2, 5), round((max(lats) + min(lats)) / 2, 5)

        if geom_type is None:
            continue

        if matched_csv_key in MANUAL_OVERRIDES:
            best_lon, best_lat = MANUAL_OVERRIDES[matched_csv_key]

        is_water = geom_type == "LineString" and any(w in raw_name.lower() or w in matched_csv_key for w in ["river", "brook", "stream", "wadi"])

        final_data = csv_locations[matched_csv_key]
        final_name = final_data["display_name"]
        
        matched_csv_keys.add(matched_csv_key) 

        # --- NEW GEOMETRY RANKING LOGIC ---
        should_update = False
        
        if final_name not in unique_names:
            should_update = True
        else:
            current_geom = unique_names[final_name]["geom_type"]
            current_mentions = unique_names[final_name]["max_mentions"]
            
            new_rank = GEOM_RANK.get(geom_type, 0)
            old_rank = GEOM_RANK.get(current_geom, 0)
            
            # If the new shape is a "higher tier" (like a Polygon vs a Point), ALWAYS update
            if new_rank > old_rank:
                should_update = True
            # If they are the same tier of shape, fall back to using the text mentions as a tie-breaker
            elif new_rank == old_rank and mentions > current_mentions:
                should_update = True
                
        if should_update:
            unique_names[final_name] = {
                "importance": final_data["importance"],
                "center": [best_lon, best_lat],
                "geom_type": geom_type,
                "geom_coords": geom_coords,
                "is_water": is_water,
                "max_mentions": mentions
            }

    features = []
    for name, data in unique_names.items():
        features.append({
            "type": "Feature",
            "geometry": {
                "type": data["geom_type"], 
                "coordinates": data["geom_coords"]
            },
            "properties": {
                "name": name,
                "importance": data["importance"],
                "center": data["center"],
                "is_water": data["is_water"]
            }
        })

    with open(OUTPUT_GEOJSON_PATH, 'w', encoding='utf-8') as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, separators=(',', ':'))

    print("\n" + "="*50)
    print("📍 MAP PROCESSING COMPLETE")
    print("="*50)
    print(f"✅ Consolidated {len(features)} uniquely named places from the CSV.")
    print(f"✅ Extracted full geometry boundaries for future game interactions.")
    print(f"✅ Saved to {OUTPUT_GEOJSON_PATH.name}!")

    missing_places = set(csv_locations.keys()) - matched_csv_keys
    if missing_places:
        print("\n" + "!"*50)
        print(f"⚠️  WARNING: {len(missing_places)} PLACES FROM YOUR CSV WERE NOT FOUND")
        print("!"*50)
        print("These places could not be matched to the KML data:")
        for missing in sorted(missing_places):
            print(f"  - {csv_locations[missing]['display_name']}")
    else:
        print("\n🎉 SUCCESS: All places in your CSV were successfully mapped!")

if __name__ == "__main__":
    kml_to_geojson()