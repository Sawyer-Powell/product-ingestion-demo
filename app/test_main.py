from fastapi.testclient import TestClient
from .main import app

client = TestClient(app)

def upload_file():
    files = {"file": ("veryfi_off_dataset.json", open("/Users/sawyer/Downloads/veryfi_off_dataset.json", "rb"), "text/plain")}
    response = client.post("/upload", files=files)
    print(response)

upload_file()
