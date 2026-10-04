import math

EARTH_RADIUS_MILES = 3958.7613

def haversine_miles(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(a))

def cumulative_route_miles(coords):
    cumulative = [0.0]
    for a, b in zip(coords, coords[1:]):
        cumulative.append(cumulative[-1] + haversine_miles(a[1], a[0], b[1], b[0]))
    return cumulative

def nearest_route_position(lat, lon, coords, cumulative):
    # Equirectangular projection around the station. Good enough for local
    # segment projection and followed by haversine distance for final checks.
    mean_lat = math.radians(lat)
    cos_lat = math.cos(mean_lat)

    best = None
    for i, (a, b) in enumerate(zip(coords, coords[1:])):
        ax = (a[0] - lon) * cos_lat
        ay = a[1] - lat
        bx = (b[0] - lon) * cos_lat
        by = b[1] - lat
        dx, dy = bx - ax, by - ay
        denom = dx * dx + dy * dy
        t = 0.0 if denom == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / denom))
        px = a[0] + t * (b[0] - a[0])
        py = a[1] + t * (b[1] - a[1])
        distance = haversine_miles(lat, lon, py, px)
        along = cumulative[i] + t * (cumulative[i + 1] - cumulative[i])
        if best is None or distance < best["distance_miles"]:
            best = {"distance_miles": distance, "along_miles": along}
    return best
