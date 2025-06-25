from fastapi.testclient import TestClient
from main import app  # Adjust import if your app is elsewhere

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    # assert response.json() == {"message": "Hello World"}  # Adjust to your actual root response

# Add more tests for your endpoints here