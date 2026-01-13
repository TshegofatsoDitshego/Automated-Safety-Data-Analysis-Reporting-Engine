import unittest
from safety_engine import evaluate_reading


class TestAlertGeneration(unittest.TestCase):

    def test_alert_created_for_critical_value(self):
        alert = evaluate_reading("S1", "LEL", 25)
        self.assertIsNotNone(alert)
        severity, _ = alert
        self.assertEqual(severity, "CRITICAL")

    def test_no_alert_for_safe_value(self):
        alert = evaluate_reading("S1", "LEL", 1)
        self.assertIsNone(alert)


if __name__ == "__main__":
    unittest.main()
