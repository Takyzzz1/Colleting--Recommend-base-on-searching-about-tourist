"""Google Maps Distance Matrix tool."""
import googlemaps
from langchain_core.tools import tool
from app.config import config


@tool
def get_distance(origin: str, destination: str, mode: str = "driving") -> dict:
    """Get travel distance and duration between two locations using Google Maps."""
    gmaps = googlemaps.Client(key=config.GOOGLE_MAPS_API_KEY)

    result = gmaps.distance_matrix(
        origins=[origin],
        destinations=[destination],
        mode=mode,
        language="vi",
    )

    element = result["rows"][0]["elements"][0]
    if element["status"] == "ZERO_RESULTS":
        raise ValueError(f"No route found from '{origin}' to '{destination}'")
    if element["status"] != "OK":
        raise RuntimeError(f"Maps API error: {element['status']}")

    return {
        "origin": origin,
        "destination": destination,
        "distance_km": round(element["distance"]["value"] / 1000, 1),
        "duration_min": round(element["duration"]["value"] / 60),
        "distance_text": element["distance"]["text"],
        "duration_text": element["duration"]["text"],
        "mode": mode,
    }
