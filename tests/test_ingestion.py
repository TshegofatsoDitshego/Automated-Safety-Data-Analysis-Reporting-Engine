import unittest
from src.ingestion.ingest_events import ingest_event

class TestIngestion(unittest.TestCase):

    def test_ingest_event_runs(self):
        event = {"type": "ACCIDENT", "severity": 2}
        ingest_event(event)
        self.assertTrue(True)
