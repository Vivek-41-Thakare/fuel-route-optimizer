from django.db import models

class FuelStation(models.Model):
    opis_id = models.BigIntegerField(db_index=True)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=500, blank=True)
    city = models.CharField(max_length=120)
    state = models.CharField(max_length=2, db_index=True)
    retail_price = models.DecimalField(max_digits=7, decimal_places=4)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    geocode_status = models.CharField(max_length=30, default="pending")
    geocode_source = models.CharField(max_length=50, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["state", "city"]),
            models.Index(fields=["latitude", "longitude"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["opis_id"], name="unique_opis_station")
        ]

    def __str__(self):
        return f"{self.name} ({self.city}, {self.state})"
