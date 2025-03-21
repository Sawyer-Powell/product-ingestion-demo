## Running locally

1. Run docker compose
```
docker-compose up
```
2. Go to web portal and upload openfoodfacts compatible JSON at 
```
http://127.0.0.1:8000
```
3. OR - Use `curl` through `sh ./scripts/upload.sh {filename.json}` 

## Running tests
```
uv run pytest
```
