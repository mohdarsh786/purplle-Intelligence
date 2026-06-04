import unittest
from events import CameraEvent

class TestEvents(unittest.TestCase):
    def test_event_schema(self):
        event = CameraEvent(
            tracker_id=999,
            zone_id="apparel",
            event_type="ZONE_ENTER",
            timestamp=1685834920.0
        )
        self.assertEqual(event.tracker_id, 999)
        self.assertEqual(event.zone_id, "apparel")
        self.assertEqual(event.event_type, "ZONE_ENTER")
        self.assertEqual(event.duration, 0.0)

if __name__ == '__main__':
    unittest.main()
