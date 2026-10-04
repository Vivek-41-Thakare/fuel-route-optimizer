from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from .serializers import RouteRequestSerializer
from .services.routing_client import OpenRouteServiceClient, RoutingError
from .services.stations import stations_near_route
from .services.optimizer import choose_fuel_stops

class RouteOptimizationView(APIView):
    def post(self, request):
        serializer = RouteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        client = OpenRouteServiceClient()
        try:
            route = client.route(data["start"], data["finish"])
            total_miles = route["distance_meters"] / 1609.344

            candidates = stations_near_route(route["geometry"])

            if total_miles > data["max_range_miles"] and not candidates:
                return Response(
                    {"detail": "No geocoded fuel stations were found near this route."},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            stops, total_cost = choose_fuel_stops(
                candidates=candidates,
                total_distance_miles=total_miles,
                max_range_miles=data["max_range_miles"],
                mpg=data["mpg"],
            )

            return Response({
                "start": route["start"],
                "finish": route["finish"],
                "route": {
                    "distance_miles": round(total_miles, 2),
                    "duration_minutes": round(route["duration_seconds"] / 60, 1),
                    "geometry": route["geometry"],
                },
                "vehicle": {
                    "max_range_miles": data["max_range_miles"],
                    "fuel_efficiency_mpg": data["mpg"],
                    "starting_tank": "full",
                    "tank_capacity_gallons": round(
                        data["max_range_miles"] / data["mpg"], 2
                    ),
                },
                "fuel_stops": stops,
                "total_money_spent": total_cost,
                "optimization": {
                    "fuel_candidates_considered": len(candidates),
                    "station_search_radius_miles": 25,
                    "routing_api_calls": route["meta"]["routing_api_calls"],
                    "route_cache_hit": route["meta"].get("cached", False),
                },
            })

        except RoutingError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
