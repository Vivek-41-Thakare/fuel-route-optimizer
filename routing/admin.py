from django.contrib import admin
from .models import FuelStation

@admin.register(FuelStation)
class FuelStationAdmin(admin.ModelAdmin):
    list_display = ("opis_id", "name", "city", "state", "retail_price", "geocode_status")
    search_fields = ("name", "city", "state", "address")
    list_filter = ("state", "geocode_status")
