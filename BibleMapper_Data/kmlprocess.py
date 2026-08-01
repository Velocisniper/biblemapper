import json
import xml.etree.ElementTree as ET
from pathlib import Path

# File paths in root directory
REPO_ROOT = Path(__file__).resolve().parent
KML_PATH = REPO_ROOT / "all_bible_places.kml"
OUTPUT_GEOJSON_PATH = REPO_ROOT / "bible_places.geojson"

def safe_get_text(element):
    """Safely extracts text from XML tags, ignoring empty nodes."""
    if element is not None and element.text is not None:
        text = element.text.strip()
        return text if text else None
    return None

def kml_to_geojson(kml_file: Path, output_file: Path):
    if not kml_file.exists():
        raise FileNotFoundError(f"Missing input file: {kml_file}")

    tree = ET.parse(kml_file)
    root = tree.getroot()
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}

    features = []

    for placemark in root.findall('.//kml:Placemark', ns):
        name_el = placemark.find('kml:name', ns)
        name = safe_get_text(name_el) or "Unnamed Place"

        point = placemark.find('.//kml:Point/kml:coordinates', ns)
        linestring = placemark.find('.//kml:LineString/kml:coordinates', ns)
        polygon = placemark.find('.//kml:Polygon//kml:coordinates', ns)

        geom_type = None
        raw_coords = None

        if point is not None:
            raw_coords = safe_get_text(point)
            if raw_coords:
                geom_type = "Point"
        elif linestring is not None:
            raw_coords = safe_get_text(linestring)
            if raw_coords:
                geom_type = "LineString"
        elif polygon is not None:
            raw_coords = safe_get_text(polygon)
            if raw_coords:
                geom_type = "Polygon"

        if not raw_coords or not geom_type:
            continue

        coords_list = []
        for pair in raw_coords.split():
            parts = [float(c) for c in pair.split(',') if c]
            if len(parts) >= 2:
                coords_list.append([parts[0], parts[1]])  # [Longitude, Latitude]

        if not coords_list:
            continue

        if geom_type == "Point":
            geometry = {"type": "Point", "coordinates": coords_list[0]}
        elif geom_type == "LineString":
            geometry = {"type": "LineString", "coordinates": coords_list}
        elif geom_type == "Polygon":
            geometry = {"type": "Polygon", "coordinates": [coords_list]}

        feature = {
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "name": name
            }
        }
        features.append(feature)

    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(geojson_data, f, indent=2)

    print(f"Successfully converted {len(features)} places to {output_file.name}!")

if __name__ == "__main__":
    kml_to_geojson(KML_PATH, OUTPUT_GEOJSON_PATH)