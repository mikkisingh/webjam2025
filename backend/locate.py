# locate.py
import os
import math
from typing import Dict, List, Optional, Tuple

import requests
from flask import Blueprint, jsonify, request

# ----- Config -----
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY", "")
DEFAULT_RADIUS_METERS = int(os.getenv("PLACES_RADIUS_METERS", "30000"))  # ~30km
MAX_RESULTS = int(os.getenv("PLACES_MAX_RESULTS", "25"))                 # frontend default

locate_bp = Blueprint("locate", __name__)  # blueprint name


# ----- Helpers -----
def haversine_miles(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    R = 3958.8
    (lat1, lon1) = (math.radians(a[0]), math.radians(a[1]))
    (lat2, lon2) = (math.radians(b[0]), math.radians(b[1]))
    dlat, dlon = (lat2 - lat1, lon2 - lon1)
    h = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return 2 * R * math.asin(min(1.0, math.sqrt(h)))


def geocode_address(q: str) -> Tuple[Optional[Dict], Optional[Tuple[Dict, int]]]:
    """Geocoding API: 'Irvine' -> {'lat':..., 'lng':..., 'formatted':...}."""
    if not GOOGLE_PLACES_API_KEY:
        return None, ({"detail": "Server missing GOOGLE_PLACES_API_KEY/GOOGLE_MAPS_API_KEY"}, 500)
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    r = requests.get(url, params={"address": q, "key": GOOGLE_PLACES_API_KEY}, timeout=15)
    r.raise_for_status()
    data = r.json()
    if not data.get("results"):
        return None, ({"detail": "Location not found"}, 404)
    top = data["results"][0]
    loc = top["geometry"]["location"]
    origin = {"lat": loc["lat"], "lng": loc["lng"], "formatted": top.get("formatted_address")}
    return origin, None


def places_search_nearby(lat: float, lng: float, radius_m: int, max_results: int = 20) -> Tuple[Optional[List[Dict]], Optional[Tuple[Dict, int]]]:
    """
    Google Places API (New) v1 nearby search.
    POST https://places.googleapis.com/v1/places:searchNearby
    Headers: X-Goog-Api-Key, X-Goog-FieldMask
    Body: includedTypes, locationRestriction.circle, maxResultCount
    """
    if not GOOGLE_PLACES_API_KEY:
        return None, ({"detail": "Server missing GOOGLE_PLACES_API_KEY/GOOGLE_MAPS_API_KEY"}, 500)

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location",
    }
    payload = {
        "includedTypes": ["hospital"],
        "maxResultCount": min(max_results, 20),  # per-page cap
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": radius_m,
            }
        },
    }

    r = requests.post(url, headers=headers, json=payload, timeout=20)
    if r.status_code >= 400:
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        return None, ({"error": "Places error", "detail": detail}, 502)

    data = r.json()
    return data.get("places", []) or [], None


# ----- Route -----
@locate_bp.get("/api/nearby")
def api_nearby():
    """
    GET /api/nearby?q=Irvine&limit=25&radius_meters=30000
    Returns: { origin, count, results: [{name, formatted, lat, lng, distance}] }
    """
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"detail": "Missing query param 'q'"}), 400

    try:
        limit = max(1, min(int(request.args.get("limit", MAX_RESULTS)), 100))
        radius_meters = max(1000, min(int(request.args.get("radius_meters", DEFAULT_RADIUS_METERS)), 80000))
    except ValueError:
        return jsonify({"detail": "Invalid numeric query params"}), 400

    origin, err = geocode_address(q)
    if err:
        body, code = err
        return jsonify(body), code

    places, err2 = places_search_nearby(origin["lat"], origin["lng"], radius_meters, max_results=min(limit, 20))
    if err2:
        body, code = err2
        return jsonify(body), code

    results: List[Dict] = []
    for p in places:
        name = (p.get("displayName") or {}).get("text") or "Unknown"
        loc = (p.get("location") or {})
        plat, plng = loc.get("latitude"), loc.get("longitude")
        if plat is None or plng is None:
            continue
        distance = haversine_miles((origin["lat"], origin["lng"]), (plat, plng))
        results.append({
            "name": name,
            "formatted": p.get("formattedAddress"),
            "lat": plat,
            "lng": plng,
            "distance": distance,
        })

    results.sort(key=lambda r: r["distance"])
    results = results[:limit]
    return jsonify({"origin": origin, "count": len(results), "results": results})
