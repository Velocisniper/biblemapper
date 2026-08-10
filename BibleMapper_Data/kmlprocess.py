import json
import math
import xml.etree.ElementTree as ET
import csv
import re
import difflib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
KML_PATH = REPO_ROOT / "all_bible_places.kml"
CSV_PATH = REPO_ROOT / "TopBibleLocations - Sheet1.csv"
OUTPUT_GEOJSON_PATH = REPO_ROOT / "bible_places.geojson"


# ================================================================
# LABEL IMPORTANCE / ZOOM RANKS
# ================================================================

# Main Anchors (Rank 1 - Zoom <= 6)
MAIN_ANCHORS = {
    "egypt",
    "achaia",
    "babylon",
    "judea",
    "judaea",
    "cyprus",
    "crete",
    "rome",
    "asia",
    "assyria",
    "persia",
}


# Mid Anchors (Rank 2 - Zoom 7)
MID_ANCHORS = {
    "jerusalem",
    "samaria",
    "malta",
    "corinth",
    "patmos",
    "ephesus",
    "colossae",
    "lystra",
    "galatia",
    "antioch",
    "damascus",
    "galilee",
    "dan",
    "beersheba",
    "midian",
    "rameses",
    "mediterranean sea",
    "athens",
    "macedonia",

    # Requested: Pisidia should be Rank 2
    "pisidia",
}


# Regional / Secondary Anchors (Rank 3 - Zoom 8)
RANK3_ANCHORS = {
    "dead sea",
    "philistia",
    "shiloh",
    "syracuse",
    "rhodes",
    "tarsus",
    "euphrates river",
    "nineveh",
    "tigris river",
    "media",
    "moab",
    "edom",
    "jordan river",
    "tyre",
    "joppa",
    "jericho",
    "red sea",
    "amalek",
    "sea of galilee",
    "thessalonica",
}


# ================================================================
# SPECIAL PLACE OVERRIDES
# ================================================================

# These are specific locations that should NOT be absorbed into
# a broader matching anchor.
#
# In particular, Pisidian Antioch is a normal Rank-4 place,
# while generic Antioch remains Rank 2.
NORMAL_PLACE_OVERRIDES = {
    "pisidian antioch",
}


# ================================================================
# CENTER OVERRIDES
# ================================================================

MANUAL_OVERRIDES = {
    "sea of galilee": [35.5800, 32.8000],
    "mediterranean sea": [23.7000, 34.5000],
    "dead sea": [35.4800, 31.6500],
    "judaea": [35.1000, 31.6500],
    "judea": [35.1000, 31.6500],
}


# ================================================================
# GEOMETRY RANKING
# ================================================================

# We ALWAYS want a Polygon or Line over a Point.
GEOM_RANK = {
    "Polygon": 3,
    "LineString": 2,
    "Point": 1,
}


# ================================================================
# AMBIGUOUS PLACE NAMES
# ================================================================

# These names refer to two different real-world locations.
#
# The KML uses numbered names such as:
#
#   Succoth 1 = Israel
#   Succoth 2 = Egypt
#
# and:
#
#   Antioch 1 = Antioch on the Orontes
#   Antioch 2 = Antioch in Pisidia
#
# The geometry is used here to distinguish the two surviving
# locations after matching the KML names to the CSV location.
AMBIGUOUS_PLACES = {
    "succoth": [
        {
            "variant": "egypt",
            "lon_max": 34.0,
        },
        {
            "variant": "israel",
            "lon_min": 34.0,
        },
    ],

    "antioch": [
        {
            "variant": "pisidia",
            "lon_max": 33.5,
        },
        {
            "variant": "syria",
            "lon_min": 33.5,
        },
    ],
}


def classify_variant(clean_key, lon):
    """
    Return the variant name for an ambiguous place.

    For example:
        Succoth west/east split
        Antioch in Pisidia vs Antioch on the Orontes
    """

    rules = AMBIGUOUS_PLACES.get(clean_key)

    if not rules:
        return None

    for rule in rules:

        if "lon_max" in rule and lon > rule["lon_max"]:
            continue

        if "lon_min" in rule and lon < rule["lon_min"]:
            continue

        return rule["variant"]

    return None


# ================================================================
# GEOGRAPHIC DISTANCE HELPERS
# ================================================================

EARTH_RADIUS_MILES = 3958.8


def haversine_miles(lon1, lat1, lon2, lat2):
    """
    Calculate great-circle distance between two coordinates.
    """

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        +
        math.cos(phi1)
        * math.cos(phi2)
        * math.sin(dlambda / 2) ** 2
    )

    return (
        2
        * EARTH_RADIUS_MILES
        * math.asin(math.sqrt(a))
    )


# ================================================================
# GEOMETRY HELPERS
# ================================================================

def polygon_bbox_miles(polygon_coords):
    """
    Approximate width/height in miles of a Polygon's outer ring.
    """

    ring = polygon_coords[0]

    lons = [pt[0] for pt in ring]
    lats = [pt[1] for pt in ring]

    min_lon = min(lons)
    max_lon = max(lons)

    min_lat = min(lats)
    max_lat = max(lats)

    center_lat = (min_lat + max_lat) / 2

    width_miles = (
        (max_lon - min_lon)
        * 69.0
        * math.cos(math.radians(center_lat))
    )

    height_miles = (
        (max_lat - min_lat)
        * 69.0
    )

    return width_miles, height_miles


def make_circle_polygon(
    center_lon,
    center_lat,
    radius_miles,
    num_points=48,
):
    """
    Generate a roughly circular Polygon ring.
    """

    coords = []

    lat_rad = math.radians(center_lat)

    cos_lat = math.cos(lat_rad)

    if cos_lat > 0.01:
        miles_per_deg_lon = 69.0 * cos_lat
    else:
        miles_per_deg_lon = 69.0

    miles_per_deg_lat = 69.0

    for i in range(num_points + 1):

        angle = (
            2
            * math.pi
            * i
            / num_points
        )

        dlon = (
            radius_miles
            * math.cos(angle)
            / miles_per_deg_lon
        )

        dlat = (
            radius_miles
            * math.sin(angle)
            / miles_per_deg_lat
        )

        coords.append(
            [
                round(center_lon + dlon, 5),
                round(center_lat + dlat, 5),
            ]
        )

    return [coords]


# ================================================================
# LARGE REGION HANDLING
# ================================================================

LARGE_REGION_THRESHOLD_MILES = 400

CAPPED_REGION_RADIUS_MILES = 150

LARGE_REGION_CAP_EXCLUSIONS = {
    "mediterranean sea",
    "dead sea",
    "sea of galilee",
    "red sea",
}


# ================================================================
# ISOLATED LOCATION HANDLING
# ================================================================

# If a location has no other location within this many miles,
# promote it to Rank 3 unless it was explicitly assigned Rank 1
# or Rank 2.
ISOLATION_THRESHOLD_MILES = 50


# ================================================================
# TEXT HELPERS
# ================================================================

def get_full_text(element):
    if element is not None:
        return "".join(element.itertext()).strip()

    return ""


def clean_place_name(name):
    """
    Normalize a place name for matching.
    """

    cleaned = re.sub(
        r"\(.*?\)",
        "",
        name,
    )

    cleaned = re.sub(
        r"[~%]",
        "",
        cleaned,
    )

    cleaned = re.sub(
        r"[^a-z\s]",
        "",
        cleaned.lower(),
    ).strip()

    return cleaned


# ================================================================
# MAIN PROCESSING
# ================================================================

def kml_to_geojson():

    if not KML_PATH.exists() or not CSV_PATH.exists():
        raise FileNotFoundError(
            "Missing KML or CSV file. Check your folder."
        )

    csv_locations = {}


    # ------------------------------------------------------------
    # PRE-POPULATE ANCHORS
    # ------------------------------------------------------------

    for anchor in MAIN_ANCHORS:

        csv_locations[anchor] = {
            "display_name": anchor.title(),
            "importance": 1,
            "manual_rank": True,
        }


    for anchor in MID_ANCHORS:

        csv_locations[anchor] = {
            "display_name": anchor.title(),
            "importance": 2,
            "manual_rank": True,
        }


    for anchor in RANK3_ANCHORS:

        csv_locations[anchor] = {
            "display_name": anchor.title(),
            "importance": 3,
            "manual_rank": True,
        }


    # ------------------------------------------------------------
    # CAPITALIZATION OVERRIDE
    # ------------------------------------------------------------

    if "sea of galilee" in csv_locations:

        csv_locations["sea of galilee"][
            "display_name"
        ] = "Sea of Galilee"


    # ------------------------------------------------------------
    # READ CSV
    # ------------------------------------------------------------

    with open(
        CSV_PATH,
        "r",
        encoding="utf-8",
    ) as f:

        reader = csv.reader(f)

        for row in reader:

            if not row:
                continue

            if not row[0].strip():
                continue

            display_name = row[0].strip()

            clean_csv = clean_place_name(
                display_name
            )


            if clean_csv in NORMAL_PLACE_OVERRIDES:

                rank = 4
                manual_rank = False

            elif clean_csv in MAIN_ANCHORS:

                rank = 1
                manual_rank = True

            elif clean_csv in MID_ANCHORS:

                rank = 2
                manual_rank = True

            elif clean_csv in RANK3_ANCHORS:

                rank = 3
                manual_rank = True

            else:

                rank = 4
                manual_rank = False


            if clean_csv not in csv_locations:

                csv_locations[clean_csv] = {
                    "display_name": display_name,
                    "importance": rank,
                    "manual_rank": manual_rank,
                }


    # ------------------------------------------------------------
    # PARSE KML
    # ------------------------------------------------------------

    tree = ET.parse(KML_PATH)

    root = tree.getroot()

    ns = {
        "kml": "http://www.opengis.net/kml/2.2"
    }


    unique_names = {}

    matched_csv_keys = set()


    # ------------------------------------------------------------
    # PROCESS PLACEMARKS
    # ------------------------------------------------------------

    for placemark in root.findall(
        ".//kml:Placemark",
        ns,
    ):

        name_el = placemark.find(
            "kml:name",
            ns,
        )

        raw_name = get_full_text(
            name_el
        )


        if not raw_name:
            continue


        clean_kml = clean_place_name(
            raw_name
        )


        matched_csv_key = None


        # --------------------------------------------------------
        # SPECIAL PISIDIAN ANTIOCH HANDLING
        # --------------------------------------------------------

        # Do this BEFORE generic matching because otherwise
        # "pisidian antioch" could be absorbed by the generic
        # Rank-2 "antioch" anchor.

        if clean_kml == "pisidian antioch":

            if "pisidian antioch" not in csv_locations:

                csv_locations["pisidian antioch"] = {
                    "display_name": "Pisidian Antioch",
                    "importance": 4,
                    "manual_rank": False,
                }

            matched_csv_key = "pisidian antioch"


        # --------------------------------------------------------
        # MANUAL OVERRIDES
        # --------------------------------------------------------

        elif (
            clean_kml in MANUAL_OVERRIDES
            and clean_kml in csv_locations
        ):

            matched_csv_key = clean_kml


        # --------------------------------------------------------
        # NORMAL MATCHING
        # --------------------------------------------------------

        else:

            # Sort keys by length descending so that
            # "sea of galilee" is checked before "galilee".

            sorted_keys = sorted(
                csv_locations.keys(),
                key=len,
                reverse=True,
            )


            for csv_key in sorted_keys:

                if re.search(
                    rf"\b{re.escape(csv_key)}\b",
                    clean_kml,
                ):

                    matched_csv_key = csv_key
                    break


            # Fuzzy matching fallback

            if not matched_csv_key:

                close_matches = (
                    difflib.get_close_matches(
                        clean_kml,
                        csv_locations.keys(),
                        n=1,
                        cutoff=0.85,
                    )
                )

                if close_matches:

                    matched_csv_key = (
                        close_matches[0]
                    )


        if not matched_csv_key:
            continue


        # --------------------------------------------------------
        # DESCRIPTION / REFERENCES
        # --------------------------------------------------------

        desc_el = placemark.find(
            "kml:description",
            ns,
        )

        desc_text = get_full_text(
            desc_el
        )


        mentions = (
            desc_text.count(",")
            +
            desc_text.count(";")
            +
            1
            if desc_text
            else 1
        )


        # --------------------------------------------------------
        # GEOMETRY NODES
        # --------------------------------------------------------

        pt_node = placemark.find(
            ".//kml:Point/kml:coordinates",
            ns,
        )

        line_node = placemark.find(
            ".//kml:LineString/kml:coordinates",
            ns,
        )

        poly_node = placemark.find(
            ".//kml:Polygon//kml:coordinates",
            ns,
        )


        geom_type = None
        geom_coords = None

        best_lon = None
        best_lat = None


        # --------------------------------------------------------
        # POINT
        # --------------------------------------------------------

        if pt_node is not None:

            raw = get_full_text(
                pt_node
            ).split()

            if raw:

                parts = [
                    float(c)
                    for c in raw[0].split(",")
                    if c
                ]

                if len(parts) >= 2:

                    geom_type = "Point"

                    geom_coords = [
                        parts[0],
                        parts[1],
                    ]

                    best_lon = parts[0]
                    best_lat = parts[1]


        # --------------------------------------------------------
        # LINESTRING
        # --------------------------------------------------------

        elif line_node is not None:

            raw = get_full_text(
                line_node
            ).split()

            coords = []


            for pair in raw:

                parts = [
                    float(c)
                    for c in pair.split(",")
                    if c
                ]

                if len(parts) >= 2:

                    coords.append(
                        [
                            parts[0],
                            parts[1],
                        ]
                    )


            if coords:

                geom_type = "LineString"

                geom_coords = coords

                mid = len(coords) // 2

                best_lon = coords[mid][0]
                best_lat = coords[mid][1]


        # --------------------------------------------------------
        # POLYGON
        # --------------------------------------------------------

        elif poly_node is not None:

            raw = get_full_text(
                poly_node
            ).split()

            coords = []

            lons = []
            lats = []


            for pair in raw:

                parts = [
                    float(c)
                    for c in pair.split(",")
                    if c
                ]

                if len(parts) >= 2:

                    coords.append(
                        [
                            parts[0],
                            parts[1],
                        ]
                    )

                    lons.append(parts[0])
                    lats.append(parts[1])


            if coords:

                geom_type = "Polygon"

                geom_coords = [
                    coords
                ]

                best_lon = round(
                    (
                        max(lons)
                        +
                        min(lons)
                    ) / 2,
                    5,
                )

                best_lat = round(
                    (
                        max(lats)
                        +
                        min(lats)
                    ) / 2,
                    5,
                )


        if geom_type is None:
            continue


        # --------------------------------------------------------
        # CENTER OVERRIDES
        # --------------------------------------------------------

        if matched_csv_key in MANUAL_OVERRIDES:

            best_lon, best_lat = (
                MANUAL_OVERRIDES[
                    matched_csv_key
                ]
            )


        # --------------------------------------------------------
        # WATER DETECTION
        # --------------------------------------------------------

        is_water = (
            geom_type == "LineString"
            and any(
                w in raw_name.lower()
                or w in matched_csv_key
                for w in [
                    "river",
                    "brook",
                    "stream",
                    "wadi",
                ]
            )
        )


        # --------------------------------------------------------
        # FINAL PLACE DATA
        # --------------------------------------------------------

        final_data = csv_locations[
            matched_csv_key
        ]

        final_name = final_data[
            "display_name"
        ]


        # --------------------------------------------------------
        # AMBIGUOUS LOCATION HANDLING
        # --------------------------------------------------------

        variant = classify_variant(
            matched_csv_key,
            best_lon,
        )


        if variant:

            unique_key = (
                f"{final_name}|{variant}"
            )

        else:

            unique_key = final_name


        matched_csv_keys.add(
            matched_csv_key
        )


        # --------------------------------------------------------
        # GEOMETRY RANKING
        # --------------------------------------------------------

        should_update = False


        if unique_key not in unique_names:

            should_update = True

        else:

            current_geom = unique_names[
                unique_key
            ]["geom_type"]

            current_mentions = unique_names[
                unique_key
            ]["max_mentions"]


            new_rank = GEOM_RANK.get(
                geom_type,
                0,
            )

            old_rank = GEOM_RANK.get(
                current_geom,
                0,
            )


            if new_rank > old_rank:

                should_update = True

            elif (
                new_rank == old_rank
                and mentions > current_mentions
            ):

                should_update = True


        if should_update:

            unique_names[unique_key] = {

                "display_name":
                    final_name,

                "clean_key":
                    matched_csv_key,

                "match_variant":
                    variant,

                "importance":
                    final_data[
                        "importance"
                    ],

                "manual_rank":
                    final_data.get(
                        "manual_rank",
                        False,
                    ),

                "center": [
                    best_lon,
                    best_lat,
                ],

                "geom_type":
                    geom_type,

                "geom_coords":
                    geom_coords,

                "is_water":
                    is_water,

                "max_mentions":
                    mentions,
            }


    # ================================================================
    # PROMOTE ISOLATED LOCATIONS
    # ================================================================

    # This happens AFTER all duplicate/variant locations have been
    # consolidated.
    #
    # Any location with no OTHER location within 50 miles becomes
    # Rank 3, unless it was explicitly assigned Rank 1 or Rank 2.
    #
    # Rank 3 locations remain Rank 3.
    #
    # Rank 4 isolated locations are promoted to Rank 3.

    location_items = list(
        unique_names.items()
    )


    isolated_promotions = []


    for name, data in location_items:

        current_importance = data[
            "importance"
        ]


        # Never override an explicitly assigned Rank 1 or Rank 2.

        if (
            current_importance <= 2
            and data.get(
                "manual_rank",
                False,
            )
        ):
            continue


        center = data.get(
            "center"
        )


        if not center or len(center) < 2:
            continue


        nearest_distance = float(
            "inf"
        )


        for (
            other_name,
            other_data,
        ) in location_items:

            if other_name == name:
                continue


            other_center = other_data.get(
                "center"
            )


            if (
                not other_center
                or len(other_center) < 2
            ):
                continue


            distance = haversine_miles(
                center[0],
                center[1],
                other_center[0],
                other_center[1],
            )


            if distance < nearest_distance:

                nearest_distance = distance


        if (
            nearest_distance
            > ISOLATION_THRESHOLD_MILES
            and current_importance > 2
        ):

            unique_names[name][
                "importance"
            ] = 3

            isolated_promotions.append(
                (
                    name,
                    nearest_distance,
                )
            )


    # ================================================================
    # BUILD GEOJSON
    # ================================================================

    features = []


    for name, data in unique_names.items():

        features.append({

            "type": "Feature",

            "geometry": {

                "type":
                    data["geom_type"],

                "coordinates":
                    data["geom_coords"],
            },

            "properties": {

                "name":
                    name,

                "importance":
                    data["importance"],

                "center":
                    data["center"],

                "is_water":
                    data["is_water"],
            },
        })


    # ================================================================
    # WRITE GEOJSON
    # ================================================================

    with open(
        OUTPUT_GEOJSON_PATH,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            {
                "type":
                    "FeatureCollection",

                "features":
                    features,
            },
            f,
            separators=(
                ",",
                ":",
            ),
        )


    # ================================================================
    # REPORT
    # ================================================================

    print(
        "\n" + "=" * 50
    )

    print(
        "📍 MAP PROCESSING COMPLETE"
    )

    print(
        "=" * 50
    )

    print(
        f"✅ Consolidated {len(features)} uniquely named places from the CSV."
    )

    print(
        "✅ Extracted full geometry boundaries for future game interactions."
    )

    print(
        f"✅ Saved to {OUTPUT_GEOJSON_PATH.name}!"
    )

    print(
        f"✅ Isolation threshold: "
        f"{ISOLATION_THRESHOLD_MILES} miles."
    )


    if isolated_promotions:

        print(
            f"⬆️ Promoted "
            f"{len(isolated_promotions)} "
            f"isolated locations to Rank 3:"
        )


        for (
            name,
            distance,
        ) in sorted(
            isolated_promotions,
            key=lambda x: x[1],
            reverse=True,
        ):

            print(
                f"   • {name}: nearest location is "
                f"{distance:.1f} miles away"
            )

    else:

        print(
            "ℹ️ No additional isolated locations required promotion."
        )


if __name__ == "__main__":
    kml_to_geojson()