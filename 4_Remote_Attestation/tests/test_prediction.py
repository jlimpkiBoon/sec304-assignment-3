"""Updated model contract: distance to station, pinned file hash, input checks."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))
import server  # noqa: E402

MODEL_BYTES = (ROOT / 'model_owner' / 'model.example.json').read_bytes()
HOUSE = {'area_m2': 120, 'bedrooms': 3, 'age_years': 10}


class PredictionTests(unittest.TestCase):
    def setUp(self):
        self.client = server.create_app().test_client()

    def provision(self):
        response = self.client.post('/model', data=MODEL_BYTES,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_expected_predictions_with_distance(self):
        self.provision()
        for distance, expected in ((2, 5550000.0), (5, 5250000.0)):
            with self.subTest(distance=distance):
                response = self.client.post(
                    '/predict', json={**HOUSE, 'distance_to_station_km': distance})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.get_json(), {'prediction_baht': expected})

    def test_changed_model_bytes_rejected(self):
        changed = MODEL_BYTES.replace(b'-100000', b'-100001')
        response = self.client.post('/model', data=changed,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.client.get('/health').get_json()['model_ready'])

    def test_missing_or_negative_distance_rejected(self):
        self.provision()
        for features in (HOUSE, {**HOUSE, 'distance_to_station_km': -1},
                         {**HOUSE, 'distance_to_station_km': True}):
            with self.subTest(features=features):
                response = self.client.post('/predict', json=features)
                self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
