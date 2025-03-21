# Running locally

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/#installation-methods)

2. Install project dependencies
```bash
uv sync
```
3. Start up database in docker
```bash
docker-compose up db
```
4. Create Product table in database
```bash
export DATABASE_URL="mysql+pymysql://temp:temp@127.0.0.1:3306/takehome";
uv run python -m scripts.init_db
```

