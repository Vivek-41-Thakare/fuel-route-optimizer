# Fuel Route Optimizer — Backend Django Assessment

A Django REST API that plans a US road trip and recommends cost-effective fuel stops using the supplied Spotter fuel-price dataset.

## What it does

- Accepts start and finish locations in the USA.
- Geocodes the two locations.
- Requests the driving route once from openrouteservice/HeiGIT.
- Searches the locally stored fuel-station dataset around the returned route.
- Accounts for a 500-mile maximum vehicle range and 10 MPG by default.
- Uses a greedy fuel-cost optimization strategy: buy only enough to reach a cheaper reachable station; otherwise fill the tank.
- Returns route GeoJSON, selected fuel stops, gallons purchased, per-stop cost, and total fuel cost.
- Caches completed routes so repeated requests can avoid another routing API call.

## Architecture

```text
POST /api/v1/route/
        |
        v
Django REST Framework
        |
        +----> Route service ----> HeiGIT/openrouteservice
        |          |
        |          +---- geocoding
        |          +---- driving directions
        |
        +----> Local FuelStation database
        |          |
        |          +---- route proximity filtering
        |
        +----> Fuel optimizer
                   |
                   v
              JSON response
```

## Why the routing API is not called for every station

The assessment specifically asks for fast results and minimal routing API usage. The API gets one complete route and performs station proximity/ordering locally. Fuel prices are already supplied by the assessment, so they are imported into the local database.

The supplied CSV has no latitude/longitude. A one-time management command therefore geocodes the stations using the US Census batch geocoder. The Census batch API accepts up to 10,000 records per batch, so the station import/geocoding process is separate from normal route requests.

## Dataset handling

The supplied file contains 8,151 rows and 57 state/province codes. Because the assignment is explicitly US-only, Canadian province codes are excluded.

The dataset contains duplicate OPIS Truckstop IDs. The importer treats an OPIS ID as one station and keeps the lowest supplied retail price for duplicate records.

## Setup

### 1. Clone

```bash
git clone <your-github-repository>
cd fuel-route-optimizer
```

### 2. Create environment

```bash
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Install

```bash
pip install -r requirements.txt
```

### 4. Configure

Copy `.env.example` to `.env` and set your HeiGIT/openrouteservice API key.

The current openrouteservice API base is:

```text
https://api.heigit.org/openrouteservice
```

Do not commit `.env`.

### 5. Database

```bash
python manage.py migrate
```

### 6. Import fuel data

```bash
python manage.py import_fuel_data data/fuel-prices-for-be-assessment.csv
```

### 7. Geocode fuel stations

```bash
python manage.py geocode_stations
```

This is an ingestion-time operation, not something the route endpoint repeats.

### 8. Run

```bash
python manage.py runserver
```

API:

```text
POST http://127.0.0.1:8000/api/v1/route/
```

## Example Postman request

```json
{
  "start": "New York, NY",
  "finish": "Boston, MA"
}
```

Optional parameters:

```json
{
  "start": "Chicago, IL",
  "finish": "Dallas, TX",
  "max_range_miles": 500,
  "mpg": 10
}
```

## Response shape

```json
{
  "start": {},
  "finish": {},
  "route": {
    "distance_miles": 914.32,
    "duration_minutes": 840.5,
    "geometry": {}
  },
  "vehicle": {
    "max_range_miles": 500,
    "fuel_efficiency_mpg": 10,
    "starting_tank": "full",
    "tank_capacity_gallons": 50
  },
  "fuel_stops": [],
  "total_money_spent": 123.45,
  "optimization": {
    "fuel_candidates_considered": 18,
    "station_search_radius_miles": 25,
    "routing_api_calls": 1,
    "route_cache_hit": false
  }
}
```

## Fuel-cost model

For a route distance `D` and efficiency `10 MPG`:

```text
fuel consumed = D / 10 gallons
```

The vehicle starts with a full 50-gallon tank because:

```text
500 miles / 10 MPG = 50 gallons
```

The total amount of fuel consumed is therefore fixed by route distance. The optimization changes **where the fuel is purchased**, which changes the total monetary cost.

## Tests

```bash
python manage.py test
```

## Docker

```bash
docker compose up --build
```

Then:

```text
http://127.0.0.1:8000/api/v1/route/
```

## Design decisions

### Local fuel optimization

No route API call is made for individual fuel stations. Stations are projected onto the returned route and ordered by distance from the start.

### Greedy purchase strategy

At a fuel station:

1. If a cheaper station is reachable with the remaining tank range, purchase only enough fuel to reach it.
2. If no cheaper station is reachable, fill the tank.
3. If the destination is reachable, stop buying fuel.

This is the standard continuous-fuel greedy strategy for minimizing purchase cost when stations have fixed prices and there are no station-specific detour costs.

### Limitations

The supplied fuel dataset has highway/exit descriptions rather than guaranteed street-level coordinates. Geocoding quality therefore depends on the external geocoder. The API only considers successfully geocoded stations and reports an infeasible-route error if no station chain can satisfy the 500-mile range constraint.

## API provider

Routing is provided by openrouteservice/HeiGIT, which is based on OpenStreetMap data. The implementation uses the current `api.heigit.org` endpoint rather than the deprecated `api.openrouteservice.org` hostname.
