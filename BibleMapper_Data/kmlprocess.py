import json
import math
import xml.etree.ElementTree as ET
import csv
import re
import html
import difflib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
KML_PATH = REPO_ROOT / "all_bible_places.kml"
CSV_PATH = REPO_ROOT / "TopBibleLocations - Sheet1.csv"
OUTPUT_GEOJSON_PATH = REPO_ROOT / "bible_places.geojson"

# Main Anchors (Rank 1 - Zoom <= 6)
MAIN_ANCHORS = {
    "egypt", "greece", "babylon", "judea", "judaea",
    "cyprus", "crete", "rome", "asia", "assyria", "persia", "spain", "media"
}

# Mid Anchors (Rank 2 - Zoom 7)
MID_ANCHORS = {
    "jerusalem", "samaria", "malta", "patmos", "achaia",
    "ephesus", "colossae", "lystra", "galatia", "antioch (syria)", 
    "damascus", "galilee", "dan", "beersheba", 
    "midian", "rameses", "mediterranean sea", "athens", "macedonia",
    "pisidia"
}

# Regional/Secondary Anchors (Rank 3 - Zoom 8)
RANK3_ANCHORS = {
    "dead sea", "philistia", "shiloh", "syracuse", "rhodes", "tarsus", 
    "euphrates river", "nineveh", "tigris river", "antioch (pisidia)", "moab", 
    "edom", "jordan river", "tyre", "joppa", "jericho", "red sea", "amalek",
    "sea of galilee", "thessalonica", "bethel", "corinth"
}

# Center overrides
MANUAL_OVERRIDES = {     
    "sea of galilee": [35.5800, 32.8000],
    "mediterranean sea": [23.7000, 34.5000], 
    "dead sea": [35.4800, 31.6500],
    "judaea": [35.1000, 31.6500],
    "judea": [35.1000, 31.6500], 
    "gomorrah": [35.42604,31.0904],
    "valley of siddim": [35.42604,31.1504],
    "bethel": [35.241389,31.952778]
}

# Hierarchy of shapes: We ALWAYS want a Polygon or Line over a Point
GEOM_RANK = {
    "Polygon": 3,
    "LineString": 2,
    "Point": 1
}

# ------------------------------------------------------------------
# Ambiguous KML locations.
#
# The KML is authoritative for which references belong to each
# geographic instance. We identify these from the KML folder names,
# not from longitude.
#
# scripture_name = biblical name used by the game/verse matcher
# display_name   = player-facing label only
# ------------------------------------------------------------------
AMBIGUOUS_KML_LOCATIONS = {
    "antioch 1": {
        "display_name": "Antioch (Syria)",
        "scripture_name": "Antioch",
        "variant": "syria",
    },
    "antioch 2": {
        "display_name": "Antioch (Pisidia)",
        "scripture_name": "Antioch",
        "variant": "pisidia",
    },
    "succoth 1": {
        "display_name": "Succoth (Israel)",
        "scripture_name": "Succoth",
        "variant": "israel",
    },
    "succoth 2": {
        "display_name": "Succoth (Egypt)",
        "scripture_name": "Succoth",
        "variant": "egypt",
    },
}

# ------------------------------------------------------------------
# Outside-Israel expansion pass.
#
# After the CSV pass, we run a second pass over all remaining KML
# placemarks that didn't match the CSV. Any placemark whose center
# falls outside the Israel bounding box is a candidate for inclusion,
# subject to:
#   - minimum scripture references in the KML (at least 1)
#   - proximity deduplication (must be > EXPANSION_MIN_SEPARATION_MILES
#     from every already-accepted location)
#   - a hard cap of EXPANSION_MAX_LOCATIONS total additions
#
# The bounding box is intentionally loose — it excludes the dense
# Israel/Palestine core but keeps Transjordan places that are already
# in the CSV list.
# ------------------------------------------------------------------
ISRAEL_BBOX = {
    "lon_min": 34.0,
    "lon_max": 36.3,
    "lat_min": 29.5,
    "lat_max": 33.5,
}

EXPANSION_MAX_LOCATIONS   = 250   # hard cap on new additions
EXPANSION_MIN_SEPARATION_MILES = 5  # don't add if something is already this close
EXPANSION_MIN_REFS        = 1     # must have at least this many KML scripture refs

def is_outside_israel(lon, lat):
    """Return True if the coordinate falls outside the Israel core bounding box."""
    bb = ISRAEL_BBOX
    return (
        lon < bb["lon_min"] or lon > bb["lon_max"] or
        lat < bb["lat_min"] or lat > bb["lat_max"]
    )


def clean_kml_identifier(name):
    cleaned = re.sub(r'\(.*?\)', '', name or '')
    cleaned = re.sub(r'[~%]', '', cleaned)
    cleaned = re.sub(r'[^a-z0-9\s]', '', cleaned.lower())
    return re.sub(r'\s+', ' ', cleaned).strip()

def clean_place_name(name):
    cleaned = re.sub(r'\(.*?\)', '', name or '')
    cleaned = re.sub(r'[~%]', '', cleaned)
    cleaned = re.sub(r'[^a-z\s]', '', cleaned.lower())
    return re.sub(r'\s+', ' ', cleaned).strip()

# Bible book names/abbreviations used in the KML reference URLs.
KML_BOOK_IDS = {
    "gen":"GEN","genesis":"GEN","exod":"EXO","exo":"EXO","exodus":"EXO",
    "lev":"LEV","leviticus":"LEV","num":"NUM","numbers":"NUM","deut":"DEU","deu":"DEU","deuteronomy":"DEU",
    "josh":"JOS","jos":"JOS","joshua":"JOS","judg":"JDG","jdg":"JDG","judges":"JDG",
    "ruth":"RUT","rut":"RUT","1sam":"1SA","1sa":"1SA","1samuel":"1SA","2sam":"2SA","2sa":"2SA","2samuel":"2SA",
    "1kgs":"1KI","1ki":"1KI","1kings":"1KI","2kgs":"2KI","2ki":"2KI","2kings":"2KI",
    "1chr":"1CH","1ch":"1CH","1chron":"1CH","2chr":"2CH","2ch":"2CH","2chron":"2CH",
    "ezra":"EZR","ezr":"EZR","neh":"NEH","nehemiah":"NEH","esth":"EST","est":"EST","esther":"EST",
    "job":"JOB","ps":"PSA","psa":"PSA","psalm":"PSA","psalms":"PSA","prov":"PRO","pro":"PRO","proverbs":"PRO",
    "eccl":"ECC","ecc":"ECC","ecclesiastes":"ECC","song":"SNG","sos":"SNG","sng":"SNG","songofsolomon":"SNG",
    "isa":"ISA","isaiah":"ISA","jer":"JER","jeremiah":"JER","lam":"LAM","lamentations":"LAM",
    "ezek":"EZE","eze":"EZE","dan":"DAN","daniel":"DAN","hos":"HOS","hosea":"HOS",
    "joel":"JOE","joe":"JOE","amos":"AMO","amo":"AMO","obad":"OBA","oba":"OBA","obadiah":"OBA",
    "jonah":"JON","jon":"JON","mic":"MIC","micah":"MIC","nah":"NAH","nahum":"NAH","hab":"HAB","habakkuk":"HAB",
    "zeph":"ZEP","zep":"ZEP","zephaniah":"ZEP","hag":"HAG","haggai":"HAG","zech":"ZEC","zec":"ZEC","zechariah":"ZEC",
    "mal":"MAL","malachi":"MAL",
    "matt":"MAT","mat":"MAT","matthew":"MAT","mark":"MRK","mrk":"MRK","mar":"MRK",
    "luke":"LUK","luk":"LUK","john":"JHN","jhn":"JHN",
    "acts":"ACT","act":"ACT","rom":"ROM","romans":"ROM","1cor":"1CO","1co":"1CO","1corinthians":"1CO",
    "2cor":"2CO","2co":"2CO","2corinthians":"2CO","gal":"GAL","galatians":"GAL",
    "eph":"EPH","ephesians":"EPH","phil":"PHP","php":"PHP","philippians":"PHP",
    "col":"COL","colossians":"COL","1thess":"1TH","1th":"1TH","1thessalonians":"1TH",
    "2thess":"2TH","2th":"2TH","2thessalonians":"2TH","1tim":"1TI","1ti":"1TI","1timothy":"1TI",
    "2tim":"2TI","2ti":"2TI","2timothy":"2TI","titus":"TIT","tit":"TIT","philem":"PHM","phm":"PHM","philemon":"PHM",
    "heb":"HEB","hebrews":"HEB","jas":"JAS","james":"JAS","1pet":"1PE","1pe":"1PE","1peter":"1PE",
    "2pet":"2PE","2pe":"2PE","2peter":"2PE","1john":"1JN","1jn":"1JN","2john":"2JN","2jn":"2JN",
    "3john":"3JN","3jn":"3JN","jude":"JUD","rev":"REV","revelation":"REV",
}

def extract_kml_references(text):
    if not text:
        return []

    text = html.unescape(text)
    refs = []
    seen = set()

    pattern = re.compile(r'(?:search=)([^&\"\'>\s]+)', re.IGNORECASE)

    for raw in pattern.findall(text):
        raw = html.unescape(raw).replace('%2E', '.')
        parts = raw.split('.')
        if len(parts) < 3:
            continue

        book_raw = parts[0].strip().lower()
        chapter = parts[1].strip()
        verse = parts[2].strip()
        book_id = KML_BOOK_IDS.get(book_raw)

        if not book_id:
            book_id = KML_BOOK_IDS.get(re.sub(r'[^a-z0-9]', '', book_raw))

        if not book_id:
            continue

        ref = f"{book_id} {chapter}:{verse}"
        if ref not in seen:
            seen.add(ref)
            refs.append(ref)

    return refs

def get_parent_map(root):
    return {child: parent for parent in root.iter() for child in parent}

def get_ancestor_folder_names(placemark, parent_map, ns):
    names = []
    current = parent_map.get(placemark)
    while current is not None:
        if current.tag.endswith("Folder"):
            name_el = current.find("kml:name", ns)
            folder_name = get_full_text(name_el)
            if folder_name:
                names.append(folder_name)
        current = parent_map.get(current)
    names.reverse()
    return names

def get_ambiguous_info(raw_name, ancestor_folders):
    for candidate in [raw_name] + ancestor_folders:
        key = clean_kml_identifier(candidate)
        if key in AMBIGUOUS_KML_LOCATIONS:
            return AMBIGUOUS_KML_LOCATIONS[key]
    return None

# ------------------------------------------------------------------
# Geometry helpers (distance, bounding box, synthetic circle)
# ------------------------------------------------------------------
EARTH_RADIUS_MILES = 3958.8

def haversine_miles(lon1, lat1, lon2, lat2):
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(a))

def polygon_bbox_miles(polygon_coords):
    """Approximate width/height in miles of a Polygon's outer ring."""
    ring = polygon_coords[0]
    lons = [pt[0] for pt in ring]
    lats = [pt[1] for pt in ring]
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)
    center_lat = (min_lat + max_lat) / 2
    width_miles = (max_lon - min_lon) * 69.0 * math.cos(math.radians(center_lat))
    height_miles = (max_lat - min_lat) * 69.0
    return width_miles, height_miles

def make_circle_polygon(center_lon, center_lat, radius_miles, num_points=48):
    """Generate a roughly circular Polygon ring of a given radius in miles."""
    coords = []
    lat_rad = math.radians(center_lat)
    cos_lat = math.cos(lat_rad)
    miles_per_deg_lon = 69.0 * cos_lat if cos_lat > 0.01 else 69.0
    miles_per_deg_lat = 69.0
    for i in range(num_points + 1):
        angle = 2 * math.pi * i / num_points
        dlon = (radius_miles * math.cos(angle)) / miles_per_deg_lon
        dlat = (radius_miles * math.sin(angle)) / miles_per_deg_lat
        coords.append([round(center_lon + dlon, 5), round(center_lat + dlat, 5)])
    return [coords]

# Large land-mass "empire" outlines (e.g. Persia spanning the whole map)
# get capped down to a Babylon-sized circle. Real seas/lakes are excluded
# since their full extent is legitimate, not a matching artifact.
LARGE_REGION_THRESHOLD_MILES = 400
CAPPED_REGION_RADIUS_MILES = 150
LARGE_REGION_CAP_EXCLUSIONS = {"mediterranean sea", "dead sea", "sea of galilee", "red sea"}

# Rank-4 places with nothing else nearby are hard to stumble onto while
# zoomed in, since their label only appears at max zoom. Anything with no
# neighbor within this radius gets promoted to rank 3.
ISOLATION_THRESHOLD_MILES = 20

def get_full_text(element):
    if element is not None:
        return "".join(element.itertext()).strip()
    return ""


def extract_placemark_geometry(placemark, ns):
    """
    Parse the geometry from a KML Placemark.
    Returns (geom_type, geom_coords, best_lon, best_lat) or (None, None, None, None).
    """
    pt_node   = placemark.find('.//kml:Point/kml:coordinates', ns)
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
                geom_type   = "Point"
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
            geom_type   = "LineString"
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
            geom_type   = "Polygon"
            geom_coords = [coords]
            best_lon = round((max(lons) + min(lons)) / 2, 5)
            best_lat = round((max(lats) + min(lats)) / 2, 5)

    return geom_type, geom_coords, best_lon, best_lat


def nearest_accepted_distance(lon, lat, accepted_centers):
    """Return the distance in miles to the nearest already-accepted location."""
    min_dist = float("inf")
    for (alon, alat) in accepted_centers:
        d = haversine_miles(lon, lat, alon, alat)
        if d < min_dist:
            min_dist = d
    return min_dist


def titlecase_name(raw):
    """Capitalise the first letter of each word, preserving hyphens."""
    return " ".join(
        "-".join(part.capitalize() for part in word.split("-"))
        for word in raw.split()
    )


# ------------------------------------------------------------------
# Expansion-pass name cleaning helpers
# ------------------------------------------------------------------

# KML names like "Kir 1 / Gutium (70%)" encode a confidence score.
# We reject anything below this threshold — low-confidence sites are
# speculative and would confuse the player.
EXPANSION_CONFIDENCE_THRESHOLD = 75


def extract_confidence_score(raw_name):
    """
    Return the integer confidence score from a name like 'Derbe (95%)',
    or None if no score is present.
    """
    m = re.search(r'\((\d+)%\)', raw_name)
    return int(m.group(1)) if m else None


def clean_expansion_display_name(raw_name):
    """
    Derive a clean, player-facing display name from a raw KML name.

    Rules applied in order:
      1. Take only the text before the first slash or tilde
         ('Kir 1 / Gutium' -> 'Kir 1', 'Ephesus~alt' -> 'Ephesus').
      2. Strip any parenthetical group, including confidence scores
         ('Derbe (95%)' -> 'Derbe', 'Haran (ancient city)' -> 'Haran').
      3. Strip a bare trailing integer — the KML duplicate index
         ('Kir 1' -> 'Kir', 'En-gedi 2' -> 'En-gedi').
         Numbers that are part of the canonical name ('1 Kings') are
         not at the end so they are left alone.
      4. Strip stray junk characters (%, ~).
      5. Titlecase the result, preserving hyphens.

    Returns an empty string if nothing useful remains after cleaning.
    """
    # Step 1: everything before the first slash or tilde
    name = re.split(r'[/~]', raw_name)[0].strip()
    # Step 2: remove parentheticals
    name = re.sub(r'\(.*?\)', '', name).strip()
    # Step 3: remove trailing bare integer (duplicate index)
    name = re.sub(r'\s+\d+$', '', name).strip()
    # Step 4: strip junk
    name = re.sub(r'[%~]', '', name).strip()
    # Step 5: titlecase
    return titlecase_name(name) if name else ""


def kml_to_geojson():
    if not KML_PATH.exists():
        raise FileNotFoundError(f"Missing KML file: {KML_PATH}")

    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Missing CSV file: {CSV_PATH}\n"
            "Make sure the CSV is in the same folder as this script "
            "and is named exactly 'TopBibleLocations - Sheet1.csv'."
        )

    print(f"Loading KML: {KML_PATH.name}")
    print(f"Loading CSV: {CSV_PATH.name}")

    csv_locations = {}
    
    # Pre-populate anchors with their ranks
    for anchor in MAIN_ANCHORS:
        csv_locations[anchor] = {"display_name": anchor.title(), "importance": 1}
    for anchor in MID_ANCHORS:
        csv_locations[anchor] = {"display_name": anchor.title(), "importance": 2}
    for anchor in RANK3_ANCHORS:
        csv_locations[anchor] = {"display_name": anchor.title(), "importance": 3}

    # Override for capitalization consistency
    if "sea of galilee" in csv_locations:
        csv_locations["sea of galilee"]["display_name"] = "Sea of Galilee"

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
                elif clean_csv in RANK3_ANCHORS:
                    rank = 3
                else:
                    rank = 4 # Everything else drops to the finest detail layer
                
                if clean_csv not in csv_locations:
                    csv_locations[clean_csv] = {
                        "display_name": display_name,
                        "importance": rank 
                    }

    tree = ET.parse(KML_PATH)
    root = tree.getroot()
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    parent_map = get_parent_map(root)

    unique_names = {}
    matched_csv_keys = set()

    # ================================================================
    # PASS 1 — CSV-matched locations (identical to original behaviour)
    # ================================================================
    # We also collect every placemark that did NOT match the CSV so
    # that the expansion pass can inspect them without re-parsing.
    unmatched_placemarks = []

    for placemark in root.findall('.//kml:Placemark', ns):
        name_el = placemark.find('kml:name', ns)
        raw_name = get_full_text(name_el)
        
        if not raw_name:
            continue

        clean_kml = clean_place_name(raw_name)
        ancestor_folders = get_ancestor_folder_names(
            placemark, parent_map, ns
        )
        ambiguous_info = get_ambiguous_info(
            raw_name, ancestor_folders
        )

        if ambiguous_info:
            matched_csv_key = clean_place_name(
                ambiguous_info["scripture_name"]
            )
        else:
            matched_csv_key = None

            if clean_kml in MANUAL_OVERRIDES and clean_kml in csv_locations:
                matched_csv_key = clean_kml
            else:
                sorted_keys = sorted(
                    csv_locations.keys(),
                    key=len,
                    reverse=True
                )
                for csv_key in sorted_keys:
                    if re.search(
                        rf'\b{re.escape(csv_key)}\b',
                        clean_kml
                    ):
                        matched_csv_key = csv_key
                        break

                if not matched_csv_key:
                    close_matches = difflib.get_close_matches(
                        clean_kml,
                        csv_locations.keys(),
                        n=1,
                        cutoff=0.85
                    )
                    if close_matches:
                        matched_csv_key = close_matches[0]

        if not matched_csv_key:
            # Save for expansion pass
            unmatched_placemarks.append((placemark, raw_name, clean_kml, ancestor_folders))
            continue

        desc_el = placemark.find('kml:description', ns)
        desc_text = get_full_text(desc_el)

        # References for Antioch/Succoth are stored on their KML folders.
        # Include ancestor folder descriptions so the correct references
        # stay attached to the correct geographic feature.
        reference_sources = [desc_text] if desc_text else []
        current = parent_map.get(placemark)
        while current is not None:
            folder_desc = current.find('kml:description', ns)
            folder_desc_text = get_full_text(folder_desc)
            if folder_desc_text:
                reference_sources.append(folder_desc_text)
            current = parent_map.get(current)

        all_reference_text = "\n".join(reference_sources)
        references = extract_kml_references(all_reference_text)

        mentions = (
            len(references)
            if references
            else (
                desc_text.count(',') + desc_text.count(';') + 1
                if desc_text else 1
            )
        )

        geom_type, geom_coords, best_lon, best_lat = extract_placemark_geometry(placemark, ns)

        if geom_type is None:
            continue

        # Replace oversized empire/region polygons with a synthetic circle so
        # the scoring boundary is sensible. Seas and lakes are exempt because
        # their full extent is geographically meaningful.
        if geom_type == "Polygon" and matched_csv_key not in LARGE_REGION_CAP_EXCLUSIONS:
            width_miles, height_miles = polygon_bbox_miles(geom_coords)
            if max(width_miles, height_miles) > LARGE_REGION_THRESHOLD_MILES:
                geom_coords = make_circle_polygon(
                    best_lon, best_lat, CAPPED_REGION_RADIUS_MILES
                )

        if matched_csv_key in MANUAL_OVERRIDES:
            best_lon, best_lat = MANUAL_OVERRIDES[matched_csv_key]

        is_water = geom_type == "LineString" and any(
            w in raw_name.lower() or w in matched_csv_key
            for w in ["river", "brook", "stream", "wadi"]
        )

        final_data = csv_locations[matched_csv_key]

        if ambiguous_info:
            final_name    = ambiguous_info["display_name"]
            scripture_name = ambiguous_info["scripture_name"]
            variant        = ambiguous_info["variant"]
        else:
            final_name    = final_data["display_name"]
            scripture_name = final_name

            if matched_csv_key == "antioch":
                final_name = scripture_name = "Antioch"
            elif matched_csv_key == "succoth":
                final_name = scripture_name = "Succoth"
            elif matched_csv_key == "pisidia":
                final_name = scripture_name = "Pisidia"
            elif final_name:
                final_name = final_name[:1].upper() + final_name[1:]

            variant = None

        unique_key = final_name
        matched_csv_keys.add(matched_csv_key)

        # --- GEOMETRY RANKING LOGIC ---
        should_update = False
        
        if unique_key not in unique_names:
            should_update = True
        else:
            current_geom     = unique_names[unique_key]["geom_type"]
            current_mentions = unique_names[unique_key]["max_mentions"]
            
            new_rank = GEOM_RANK.get(geom_type, 0)
            old_rank = GEOM_RANK.get(current_geom, 0)
            
            if new_rank > old_rank:
                should_update = True
            elif new_rank == old_rank and mentions > current_mentions:
                should_update = True
                
        if should_update:
            unique_names[unique_key] = {
                "display_name":  final_name,
                "scripture_name": scripture_name,
                "clean_key":     matched_csv_key,
                "match_variant": variant,
                "importance":    final_data["importance"],
                "center":        [best_lon, best_lat],
                "geom_type":     geom_type,
                "geom_coords":   geom_coords,
                "is_water":      is_water,
                "references":    references,
                "max_mentions":  mentions,
                "from_expansion": False,
            }

    print(f"  Pass 1 complete: {len(unique_names)} CSV-matched locations.")

    # ================================================================
    # PASS 2 — Outside-Israel expansion
    #
    # Walk every placemark that didn't match the CSV. For each one:
    #   1. Parse geometry; skip if none or if center is inside Israel.
    #   2. Must have at least EXPANSION_MIN_REFS scripture references.
    #   3. Must not clash with an existing location (name or proximity).
    #   4. Collect all valid candidates, sort by reference count
    #      descending (most-referenced first = most likely to appear
    #      in a verse), then admit up to EXPANSION_MAX_LOCATIONS.
    # ================================================================

    # Build a list of all current center points for proximity checks.
    accepted_centers = [
        tuple(d["center"])
        for d in unique_names.values()
        if d.get("center")
    ]

    expansion_candidates = []

    # Normalised names already in the map (for name-clash detection)
    existing_names_normalised = {
        clean_place_name(k) for k in unique_names.keys()
    }

    # Track cleaned names seen during the candidate-building phase so that
    # multiple KML placemarks that resolve to the same clean name (e.g.
    # "Kir 1" and "Kir 2") are deduplicated before we even sort.
    # The highest-confidence / most-referenced variant wins.
    expansion_by_clean_name = {}  # clean_display -> candidate dict

    skipped_confidence  = 0
    skipped_bad_name    = 0

    for placemark, raw_name, clean_kml, ancestor_folders in unmatched_placemarks:

        # ---- name cleaning & confidence filtering ----

        confidence = extract_confidence_score(raw_name)

        # Reject low-confidence speculative sites
        if confidence is not None and confidence < EXPANSION_CONFIDENCE_THRESHOLD:
            skipped_confidence += 1
            continue

        display_name = clean_expansion_display_name(raw_name)

        # Reject empty or degenerate results (e.g. the whole name was a number)
        if not display_name or display_name.isdigit():
            skipped_bad_name += 1
            continue

        # ---- geometry ----

        geom_type, geom_coords, best_lon, best_lat = extract_placemark_geometry(
            placemark, ns
        )
        if geom_type is None:
            continue

        # Must be outside Israel
        if not is_outside_israel(best_lon, best_lat):
            continue

        # ---- scripture references ----

        desc_el   = placemark.find('kml:description', ns)
        desc_text = get_full_text(desc_el)

        reference_sources = [desc_text] if desc_text else []
        current = parent_map.get(placemark)
        while current is not None:
            folder_desc = current.find('kml:description', ns)
            folder_desc_text = get_full_text(folder_desc)
            if folder_desc_text:
                reference_sources.append(folder_desc_text)
            current = parent_map.get(current)

        all_reference_text = "\n".join(reference_sources)
        references = extract_kml_references(all_reference_text)

        if len(references) < EXPANSION_MIN_REFS:
            continue

        # ---- name-clash with CSV pass ----

        norm = clean_place_name(display_name)
        if norm in existing_names_normalised:
            continue

        # ---- apply large-polygon cap ----

        if geom_type == "Polygon":
            width_miles, height_miles = polygon_bbox_miles(geom_coords)
            if max(width_miles, height_miles) > LARGE_REGION_THRESHOLD_MILES:
                geom_coords = make_circle_polygon(
                    best_lon, best_lat, CAPPED_REGION_RADIUS_MILES
                )

        is_water = geom_type == "LineString" and any(
            w in raw_name.lower()
            for w in ["river", "brook", "stream", "wadi"]
        )

        candidate = {
            "display_name":   display_name,
            "scripture_name": display_name,
            "clean_key":      norm,
            "match_variant":  None,
            "importance":     4,
            "center":         [best_lon, best_lat],
            "geom_type":      geom_type,
            "geom_coords":    geom_coords,
            "is_water":       is_water,
            "references":     references,
            "max_mentions":   len(references),
            "confidence":     confidence if confidence is not None else 100,
            "from_expansion": True,
        }

        # ---- intra-expansion deduplication ----
        # If we've already seen this cleaned name, keep whichever variant
        # has more references (then higher confidence as a tiebreaker).
        if norm in expansion_by_clean_name:
            existing = expansion_by_clean_name[norm]
            if (len(references), candidate["confidence"]) > \
               (existing["max_mentions"], existing["confidence"]):
                expansion_by_clean_name[norm] = candidate
        else:
            expansion_by_clean_name[norm] = candidate

    expansion_candidates = list(expansion_by_clean_name.values())

    print(
        f"  Expansion pre-filter: {skipped_confidence} rejected for low confidence, "
        f"{skipped_bad_name} rejected for bad/empty name, "
        f"{len(expansion_candidates)} unique candidates remaining."
    )

    # Sort by reference count descending so the most-attested places
    # fill the cap first.
    expansion_candidates.sort(key=lambda x: x["max_mentions"], reverse=True)

    added = 0
    skipped_proximity = 0

    for candidate in expansion_candidates:
        if added >= EXPANSION_MAX_LOCATIONS:
            break

        lon, lat = candidate["center"]

        # Proximity check against everything accepted so far
        if accepted_centers:
            nearest = nearest_accepted_distance(lon, lat, accepted_centers)
            if nearest < EXPANSION_MIN_SEPARATION_MILES:
                skipped_proximity += 1
                continue

        norm = candidate["clean_key"]
        unique_key = candidate["display_name"]
        unique_names[unique_key] = candidate
        accepted_centers.append(tuple(candidate["center"]))
        existing_names_normalised.add(norm)
        added += 1

    print(
        f"  Pass 2 complete: {added} expansion locations added "
        f"({skipped_proximity} skipped for proximity)."
    )
    print(f"  Total before isolation pass: {len(unique_names)}")

    # --------------------------------------------------------------
    # Promote isolated Rank-4 places to Rank 3.
    #
    # Any place with no other mapped location within
    # ISOLATION_THRESHOLD_MILES gets promoted so its label appears
    # at zoom 8 rather than only at max zoom.
    # Explicit Rank 1/2/3 locations are never changed.
    # --------------------------------------------------------------
    place_items = list(unique_names.items())

    for name, data in place_items:
        if data["importance"] < 4:
            continue

        center = data.get("center")
        if not center:
            continue

        nearest_miles = float("inf")

        for other_name, other_data in place_items:
            if other_name == name:
                continue

            other_center = other_data.get("center")
            if not other_center:
                continue

            distance = haversine_miles(
                center[0],
                center[1],
                other_center[0],
                other_center[1]
            )

            if distance < nearest_miles:
                nearest_miles = distance

        if nearest_miles > ISOLATION_THRESHOLD_MILES:
            data["importance"] = 3

    features = []
    for name, data in unique_names.items():
        features.append({
            "type": "Feature",
            "geometry": {
                "type":        data["geom_type"], 
                "coordinates": data["geom_coords"]
            },
            "properties": {
                "name":              data["display_name"],
                "scripture_name":    data["scripture_name"],
                "importance":        data["importance"],
                "center":            data["center"],
                "is_water":          data["is_water"],
                "references":        data.get("references", []),
                "location_variant":  data.get("match_variant")
            }
        })

    with open(OUTPUT_GEOJSON_PATH, 'w', encoding='utf-8') as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, separators=(',', ':'))

    print("\n" + "="*50)
    print("📍 MAP PROCESSING COMPLETE")
    print("="*50)
    print(f"✅ {len(features)} total locations written to {OUTPUT_GEOJSON_PATH.name}")

    print("\nSpecial locations:")
    for special_name in (
        "Antioch (Syria)",
        "Antioch (Pisidia)",
        "Succoth (Israel)",
        "Succoth (Egypt)",
        "Pisidia",
    ):
        found = [
            d for d in unique_names.values()
            if d["display_name"] == special_name
        ]
        if found:
            d = found[0]
            print(
                f"  ✓ {special_name} | "
                f"scripture_name={d['scripture_name']} | "
                f"references={len(d.get('references', []))} | "
                f"rank={d['importance']}"
            )
        else:
            print(f"  ✗ {special_name} NOT FOUND")

    # Show a sample of what was added in the expansion pass
    expansion_added = [
        d for d in unique_names.values()
        if d.get("from_expansion")
    ]
    if expansion_added:
        expansion_added.sort(key=lambda x: x["max_mentions"], reverse=True)
        print(f"\nTop 20 expansion additions (by reference count):")
        for d in expansion_added[:20]:
            print(
                f"  + {d['display_name']} "
                f"({d['max_mentions']} refs, "
                f"lon={d['center'][0]:.2f}, lat={d['center'][1]:.2f})"
            )

if __name__ == "__main__":
    kml_to_geojson()