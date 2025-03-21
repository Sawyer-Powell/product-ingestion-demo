import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import json
from app.main import app
from fastapi.openapi.utils import get_openapi

if __name__ == "__main__":
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    with open("openapi.json", "w") as file:
        json.dump(openapi_schema, file, indent=4)

    print("OpenAPI JSON schema saved to openapi.json")
