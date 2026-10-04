import math
from .geo import cumulative_route_miles, nearest_route_position
from .optimizer import Candidate
from ..models import FuelStation

def stations_near_route(route_geometry, radius_miles=25.0):
    coords = route_geometry["coordinates"]
    cumulative = cumulative_route_miles(coords)

    lats = [c[1] for c in coords]
    lons = [c[0] for c in coords]
    # 1 degree latitude is ~69 miles. Longitude is adjusted conservatively.
    lat_margin = radius_miles / 69.0
    mid_lat = math.radians(sum(lats) / len(lats))
    lon_margin = radius_miles / (69.0 * max(math.cos(mid_lat), 0.2))

    qs = FuelStation.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False,
        latitude__gte=min(lats) - lat_margin,
        latitude__lte=max(lats) + lat_margin,
        longitude__gte=min(lons) - lon_margin,
        longitude__lte=max(lons) + lon_margin,
    ).only(
        "id", "opis_id", "name", "city", "state",
        "retail_price", "latitude", "longitude"
    )

    candidates = []
    for station in qs.iterator(chunk_size=1000):
        match = nearest_route_position(
            station.latitude, station.longitude, coords, cumulative
        )
        if match and match["distance_miles"] <= radius_miles:
            candidates.append(Candidate(
                station_id=station.opis_id,
                name=station.name,
                city=station.city,
                state=station.state,
                latitude=station.latitude,
                longitude=station.longitude,
                price=float(station.retail_price),
                along_miles=match["along_miles"],
                route_distance_miles=match["distance_miles"],
            ))

    return candidates
