## Running locally

1. Run docker compose
```
docker-compose up
```
3. Use `curl` through `sh ./scripts/upload.sh {filename.json}` 

2. OR - Go to web portal and upload openfoodfacts compatible JSON at 
```
http://127.0.0.1:8000
```

## Running tests
```
uv sync
uv run pytest
```
# Design Notes

This service provides one endpoint, `/upload`, which accepts a file upload. 

Upon receiving the file: 
- The service validates the JSON
- Filters the data according to quality criteria
- Cleans/normalizes the data
- Serializes the data to a postgres database

If the system encounters an item with the same id already existing in the
database, it overwrites it. Maintaining a history of changes across ids
might be useful for data science teams and customers, but is likely tangential 
to the goal of matching receipt data to arbitrary product data, and comes 
with significant space and complexity tradeoffs.

At the moment, the system writes to its own postgres database, but could
be easily modified through a change in the connection string to point
at an existing database.

In the postgres database there are three tables
- product
- country
- producttocountry

The system offers facilities to easily group products by country of
origin(s) to make downstream queries easier as the dataset grows.

This serves as a proof of concept for how this system can adapt to
encoding many-to-many relationships that appear in the datasest. The
"brand" column also demonstrates this many-to-many relationship with product.

## Notes on scale

The provided dataset weighs in at ~113M on disk. After being processed
by the system a `sqlite` database containing nearly the same amount of items
has a size of ~17M.

Assuming we get a new dataset each week, our worst case scenario is an increase
of ~20M per week rounding up. Over the course of a year, this leads us to a db
size of ~1GB. 1GB (worst case) increase per year is extremely manageable, 
and doesn't warrant serious consideration concerning sharding/distributing 
the dataset.

## Integrating with other systems

This project is based around `FastAPI` which provides excellent facilities for generating `OpenAPI` compatible JSON files from endpoints.
This JSON can be used to generate client stub code for use by other services. 
