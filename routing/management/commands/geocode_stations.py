import csv
import io
import requests

from django.core.management.base import BaseCommand, CommandError
from routing.models import FuelStation

CENSUS_URL = "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"
BENCHMARK = "Public_AR_Current"

class Command(BaseCommand):
    help = "Geocode pending fuel stations using the US Census batch geocoder."

    def handle(self, *args, **options):
        stations = list(
            FuelStation.objects.filter(
                latitude__isnull=True,
                longitude__isnull=True,
                geocode_status="pending",
            )
        )
        if not stations:
            self.stdout.write("No pending stations.")
            return

        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")
        for station in stations:
            # The supplied dataset often contains highway/exit descriptions
            # rather than a conventional street number. We retain that exact
            # value; Census may match it, otherwise it remains un-geocoded.
            writer.writerow([
                station.opis_id,
                station.address or f"{station.city}, {station.state}",
                station.city,
                station.state,
                "",
            ])

        files = {
            "addressFile": (
                "stations.csv",
                output.getvalue().encode("utf-8"),
                "text/csv",
            )
        }
        params = {
            "benchmark": BENCHMARK,
            "vintage": "Current_Current",
        }

        response = requests.post(CENSUS_URL, params=params, files=files, timeout=120)
        if response.status_code != 200:
            raise CommandError(
                f"Census geocoder returned HTTP {response.status_code}: "
                f"{response.text[:500]}"
            )

        reader = csv.reader(io.StringIO(response.text))
        by_id = {str(s.opis_id): s for s in stations}
        matched = failed = 0

        for row in reader:
            if len(row) < 6:
                continue
            station = by_id.get(row[0].strip())
            if not station:
                continue

            match = row[2].strip().lower()
            if match == "match":
                try:
                    lon, lat = [float(x.strip()) for x in row[5].split(",")]
                    station.longitude = lon
                    station.latitude = lat
                    station.geocode_status = "matched"
                    station.geocode_source = "us_census_batch"
                    station.save(update_fields=[
                        "longitude", "latitude", "geocode_status", "geocode_source"
                    ])
                    matched += 1
                except (ValueError, IndexError):
                    station.geocode_status = "failed"
                    station.save(update_fields=["geocode_status"])
                    failed += 1
            else:
                station.geocode_status = "failed"
                station.save(update_fields=["geocode_status"])
                failed += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Geocoding complete: {matched} matched, {failed} failed."
            )
        )
