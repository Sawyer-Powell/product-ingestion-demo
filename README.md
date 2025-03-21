## Running locally

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/#installation-methods)

2. Install project dependencies
```bash
uv sync
```
3. Run docker compose
```
docker-compose up
```
4. Initialize db tables
```
export DATABASE_URL="postgresql://temp:temp@127.0.0.1:5432/takehome"
uv run python -m scripts.init_db
```
5. Go to web portal and upload openfoodfacts compatible JSON at 
```
http://127.0.0.1:8000
```

6. OR - Use `curl` through `sh ./scripts/upload.sh {filename.json}` 


## Running tests
```
uv run pytest
```
