import csv
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from routing.models import FuelStation

US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN",
    "IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV",
    "NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN",
    "TX","UT","VT","VA","WA","WV","WI","WY","DC"
}

class Command(BaseCommand):
    help = "Import the Spotter fuel-price CSV into the database."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str)

    def handle(self, *args, **options):
        path = Path(options["csv_path"])
        if not path.exists():
            raise CommandError(f"File not found: {path}")

        rows = {}
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            required = {
                "OPIS Truckstop ID", "Truckstop Name", "Address",
                "City", "State", "Retail Price"
            }
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise CommandError(f"Missing columns: {sorted(missing)}")

            for row in reader:
                state = row["State"].strip().upper()
                if state not in US_STATES:
                    continue
                opis_id = int(row["OPIS Truckstop ID"])
                price = Decimal(row["Retail Price"])
                current = rows.get(opis_id)
                # Duplicate OPIS IDs exist. Treat them as one physical station
                # and keep the lowest supplied retail price.
                if current is None or price < current["retail_price"]:
                    rows[opis_id] = {
                        "opis_id": opis_id,
                        "name": row["Truckstop Name"].strip(),
                        "address": row["Address"].strip(),
                        "city": row["City"].strip(),
                        "state": state,
                        "retail_price": price,
                    }

        created = updated = 0
        for station in rows.values():
            obj, was_created = FuelStation.objects.update_or_create(
                opis_id=station["opis_id"],
                defaults=station,
            )
            created += int(was_created)
            updated += int(not was_created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {len(rows)} unique US stations "
                f"({created} created, {updated} updated)."
            )
        )
