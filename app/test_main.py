from fastapi.testclient import TestClient
from .main import app

client = TestClient(app)

def test_upload_malformed_file():
    files = {"file": ("veryfi_off_dataset.json", open("/Users/sawyer/Documents/fasthtml-fig1.svg", "rb"), "text/plain")}
    response = client.post("/upload", files=files)
    assert response.status_code != 200

def upload_file():
    files = {"file": ("veryfi_off_dataset.json", open("/Users/sawyer/Downloads/veryfi_off_dataset.json", "rb"), "text/plain")}
    response = client.post("/upload", files=files)
    assert response.status_code == 200

upload_file()
