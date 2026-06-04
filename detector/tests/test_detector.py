import unittest
from detector import YOLODetector

class TestYOLODetector(unittest.TestCase):
    def test_detector_initialization(self):
        detector = YOLODetector()
        self.assertTrue(detector.is_mock)
        self.assertEqual(detector.model_path, "models/yolov8n.pt")

if __name__ == '__main__':
    unittest.main()
