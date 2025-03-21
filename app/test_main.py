import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"


from fastapi.testclient import TestClient
from .main import app
from .db import create_tables

create_tables()

client = TestClient(app)


def test_upload_malformed_file():
    files = {
        "file": (
            "malformed.json",
            open("./test_files/malformed.json", "rb"),
            "text/plain",
        )
    }
    response = client.post("/upload/", files=files)
    assert response.status_code != 200


def test_upload_file():
    files = {
        "file": (
            "correct.json",
            open("./test_files/correct.json", "rb"),
            "text/plain",
        )
    }
    response = client.post("/upload/", files=files)
    assert response.status_code == 200


if __name__ == "__main__":
    test_upload_file()
