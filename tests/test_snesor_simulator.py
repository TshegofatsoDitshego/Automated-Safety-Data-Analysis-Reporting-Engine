import unittest
from sensor_simulator import generate_reading


class TestSensorSimulator(unittest.TestCase):

    def test_sensor_reading_has_required_fields(self):
        reading = generate_reading()
        self.assertIn("sensor_id", reading)
        self.assertIn("gas_type", reading)
        self.assertIn("value", reading)
        self.assertIn("timestamp", reading)

    def test_sensor_value_is_never_negative(self):
        for _ in range(100):
            reading = generate_reading()
            self.assertGreaterEqual(reading["value"], 0)


if __name__ == "__main__":
    unittest.main()
