from fastapi.testclient import TestClient
import sys
import os

# Append paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)

def test_read_metrics():
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "footfall" in data
    assert "avg_dwell_minutes" in data
    assert "conversion_rate" in data
