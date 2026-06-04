import unittest
from tracker import CentroidTracker

class TestTracker(unittest.TestCase):
    def test_registration(self):
        tracker = CentroidTracker()
        rects = [[10, 10, 50, 50]]
        objects = tracker.update(rects)
        self.assertEqual(len(objects), 1)
        self.assertIn(1000, objects)

    def test_deregistration(self):
        tracker = CentroidTracker(max_disappeared=2)
        rects = [[10, 10, 50, 50]]
        tracker.update(rects)
        # Update with empty rects to trigger disappeared increments
        tracker.update([])
        objects = tracker.update([])
        # Object should now be deregistered since max_disappeared = 2
        self.assertEqual(len(objects), 0)

if __name__ == '__main__':
    unittest.main()
