import hashlib
import json
import time
from django.conf import settings
from django.core.cache import cache
import requests

class RoutingError(Exception):
    pass

class OpenRouteServiceClient:
    def __init__(self):
        self.base_url = settings.ORS_BASE_URL.rstrip("/")
        self.api_key = settings.ORS_API_KEY

    def _cache_key(self, start, finish):
        raw = f"{start.strip().lower()}|{finish.strip().lower()}"
        return "route:" + hashlib.sha256(raw.encode()).hexdigest()

    def geocode(self, text):
        if not self.api_key:
            raise RoutingError("ORS_API_KEY is not configured.")

        url = "https://api.heigit.org/pelias/v1/search"
        params = {"text": text, "size": 1}
        response = requests.get(
            url,
            params=params,
            headers={"Authorization": self.api_key},
            timeout=15,
        )
        if response.status_code != 200:
            raise RoutingError(f"Geocoding failed with HTTP {response.status_code}.")
        features = response.json().get("features", [])
        if not features:
            raise RoutingError(f"Could not geocode location: {text}")
        coords = features[0]["geometry"]["coordinates"]
        return {"label": features[0]["properties"].get("label", text),
                "longitude": coords[0], "latitude": coords[1]}

    def route(self, start, finish):
        key = self._cache_key(start, finish)
        cached = cache.get(key)
        if cached:
            cached["meta"]["routing_api_calls"] = 0
            cached["meta"]["cached"] = True
            return cached

        start_point = self.geocode(start)
        finish_point = self.geocode(finish)

        url = f"{self.base_url}/v2/directions/driving-car/geojson"
        payload = {
            "coordinates": [
                [start_point["longitude"], start_point["latitude"]],
                [finish_point["longitude"], finish_point["latitude"]],
            ],
            "instructions": False,
            "geometry": True,
        }
        response = requests.post(
            url,
            json=payload,
            headers={
                "Authorization": self.api_key,
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        if response.status_code != 200:
            raise RoutingError(
                f"Directions failed with HTTP {response.status_code}: "
                f"{response.text[:300]}"
            )

        data = response.json()
        feature = data["features"][0]
        summary = feature["properties"]["summary"]

        result = {
            "start": start_point,
            "finish": finish_point,
            "geometry": feature["geometry"],
            "distance_meters": float(summary["distance"]),
            "duration_seconds": float(summary["duration"]),
            "meta": {"routing_api_calls": 1, "cached": False},
        }
        cache.set(key, result, settings.ROUTE_CACHE_SECONDS)
        return result


