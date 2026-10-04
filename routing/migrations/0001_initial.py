from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="FuelStation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("opis_id", models.BigIntegerField(db_index=True)),
                ("name", models.CharField(max_length=255)),
                ("address", models.CharField(blank=True, max_length=500)),
                ("city", models.CharField(max_length=120)),
                ("state", models.CharField(db_index=True, max_length=2)),
                ("retail_price", models.DecimalField(decimal_places=4, max_digits=7)),
                ("latitude", models.FloatField(blank=True, null=True)),
                ("longitude", models.FloatField(blank=True, null=True)),
                ("geocode_status", models.CharField(default="pending", max_length=30)),
                ("geocode_source", models.CharField(blank=True, max_length=50)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["state", "city"], name="routing_fue_state_7a5d3b_idx"),
                    models.Index(fields=["latitude", "longitude"], name="routing_fue_latitu_6c3b44_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(fields=("opis_id",), name="unique_opis_station")
                ],
            },
        ),
    ]
