from django.test import TestCase
from .services.optimizer import Candidate, choose_fuel_stops

class OptimizerTests(TestCase):
    def test_short_route_needs_no_stop(self):
        stops, cost = choose_fuel_stops([], 300, 500, 10)
        self.assertEqual(stops, [])
        self.assertEqual(cost, 0)

    def test_chooses_cheaper_station_within_range(self):
        candidates = [
            Candidate(1, "Expensive", "A", "TX", 0, 0, 4.00, 100, 1),
            Candidate(2, "Cheap", "B", "TX", 0, 0, 3.00, 300, 1),
            Candidate(3, "Later", "C", "TX", 0, 0, 5.00, 650, 1),
        ]
        stops, cost = choose_fuel_stops(candidates, 900, 500, 10)
        self.assertTrue(stops)
        self.assertEqual(stops[0]["station_id"], 2)
        self.assertGreater(cost, 0)

    def test_detects_unreachable_gap(self):
        candidates = [
            Candidate(1, "A", "A", "TX", 0, 0, 3.0, 100, 1),
            Candidate(2, "B", "B", "TX", 0, 0, 3.0, 700, 1),
        ]
        with self.assertRaises(ValueError):
            choose_fuel_stops(candidates, 900, 500, 10)
