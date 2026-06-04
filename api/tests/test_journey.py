from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)

def test_read_journey():
    response = client.get("/api/journey")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "tracker_id" in data[0]
