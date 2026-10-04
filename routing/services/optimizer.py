from dataclasses import dataclass

@dataclass(frozen=True)
class Candidate:
    station_id: int
    name: str
    city: str
    state: str
    latitude: float
    longitude: float
    price: float
    along_miles: float
    route_distance_miles: float

def choose_fuel_stops(candidates, total_distance_miles, max_range_miles=500.0, mpg=10.0):
    if total_distance_miles <= max_range_miles:
        return [], 0.0

    tank_gallons = max_range_miles / mpg
    ordered = sorted(
        [s for s in candidates if 0.5 < s.along_miles < total_distance_miles - 0.5],
        key=lambda s: s.along_miles,
    )

    # Add destination as a virtual zero-price purchase-free node.
    destination = Candidate(
        station_id=-1, name="Destination", city="", state="",
        latitude=0.0, longitude=0.0, price=float("inf"),
        along_miles=total_distance_miles, route_distance_miles=0.0,
    )
    nodes = ordered + [destination]

    # Feasibility check: every gap between origin/stations/destination must
    # have at least one station within max range.
    if not nodes or nodes[0].along_miles > max_range_miles:
        raise ValueError("No fuel station is reachable from the starting point.")
    for a, b in zip(nodes, nodes[1:]):
        if b.along_miles - a.along_miles > max_range_miles + 1e-6:
            raise ValueError(
                f"No fuel station is reachable across the {b.along_miles-a.along_miles:.1f}-mile gap."
            )
    if total_distance_miles - nodes[-2].along_miles > max_range_miles + 1e-6:
        raise ValueError("The destination cannot be reached from the last available fuel station.")

    # At each station:
    # - If a cheaper station is reachable, buy only enough to reach it.
    # - Otherwise fill the tank, because this station is the cheapest reachable
    #   purchase opportunity before a more expensive/farther stop.
    current_pos = 0.0
    fuel = tank_gallons
    current_station = None
    stops = []
    total_cost = 0.0

    while current_pos < total_distance_miles - 1e-6:
        reachable = [
            s for s in nodes
            if s.along_miles > current_pos + 1e-6
            and s.along_miles - current_pos <= max_range_miles + 1e-6
        ]
        if not reachable:
            raise ValueError("No reachable station/destination within vehicle range.")

        if current_station is None:
            # Starting with a full tank: choose the cheapest station that can
            # be reached before the tank is empty. If the destination is in
            # range, no purchase is needed at all.
            if any(s.station_id == -1 for s in reachable):
                return [], 0.0
            target = min(reachable, key=lambda s: (s.price, -s.along_miles))
            distance = target.along_miles - current_pos
            fuel -= distance / mpg
            current_pos = target.along_miles
            current_station = target
            continue

        cheaper = [s for s in reachable if s.station_id != -1 and s.price < current_station.price - 1e-9]
        if cheaper:
            target = min(cheaper, key=lambda s: s.along_miles)
        else:
            target = min(reachable, key=lambda s: s.along_miles)

        distance = target.along_miles - current_pos
        gallons_needed = distance / mpg

        if gallons_needed > fuel + 1e-9:
            # This should only happen if the previous station was chosen at
            # the edge of reachability. Top up enough to make the trip.
            buy = gallons_needed - fuel
        elif cheaper:
            buy = max(0.0, gallons_needed - fuel)
        else:
            buy = tank_gallons - fuel

        if buy > 1e-9:
            cost = buy * current_station.price
            total_cost += cost
            stops.append({
                "station_id": current_station.station_id,
                "name": current_station.name,
                "city": current_station.city,
                "state": current_station.state,
                "latitude": current_station.latitude,
                "longitude": current_station.longitude,
                "distance_from_start_miles": round(current_station.along_miles, 2),
                "price_per_gallon": round(current_station.price, 4),
                "gallons_purchased": round(buy, 3),
                "cost": round(cost, 2),
            })
            fuel += buy

        fuel -= gallons_needed
        if fuel < -1e-6:
            raise ValueError("Fuel optimization produced an infeasible segment.")

        current_pos = target.along_miles
        if target.station_id == -1:
            break
        current_station = target

    return stops, round(total_cost, 2)
