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

## Extending the system

This system uses a couple of techniques to allow it to adapt to changes in features
and scale.

1. Decoupling of data representations

    Authoritative Python representations of the tables in the database are
    available in `app/db.py`, which differ from the `Pydantic` representation
    of the openfoodfacts product data available in `app/ingest.py`. If the system
    needs to support new datasets, that new dataset can be forced into compliance
    with the database representation, or minor modifications can be made to the
    db schema.

2. Type safety

    Type annotations are used as much as possible throughout the codebase to
    catch bugs early, and facilitate refactors. Type safety in this project has
    another benefit, it dovetails with `FastAPI`'s `OpenAPI` schema
    generation tools.

    When data teams and customers are provided with endpoints to
    query data out of this service, the system's `OpenAPI` schema will always be
    up to date with its internal data structures.

3. Internal ETL pipeline built around the generator pattern

    This system makes used of the `ijson` library to iteratively parse
    uploaded files as chunks are received over the network. In `app/ingest.py`,
    `parse_products` produces a generator that can be iterated through by
    `to_db`.

    The `parse_products` function calls `transform_product`, which offers
    the programmer a convenient method to adjust how raw data is getting
    normalized/cleaned and filtered before being sent to the db.

    This pattern is well suited to expansion, offering convenient avenues
    for adding features like data enrichment, or parallelization/pipelining 
    over multiple cores/compute nodes.

## Notes on scale

The provided dataset weighs in at ~113M on disk. After being processed
by the system a `sqlite` database containing nearly the same amount of items
has a size of ~17M.

Assuming we get a new dataset each week, our worst case scenario is an increase
of ~20M per week rounding up. Over the course of a year, this leads us to a db
size of ~1GB. 1GB (worst case) increase per year is extremely manageable, 
and doesn't warrant serious consideration concerning sharding/distributing 
the dataset.

### How this system can be scaled up to 100x+

#### If we're still just getting weekly uploads, but those uploads are larger

1. Find data to archive. Our records have a "last_modified" time, using that metric
we might be able to find a good amount of products that can be warehoused.
2. We could also consider data fragmentation strategies. Postgres offers
a number of data fragmentation tools, which would require some infra restructuring,
depending on if we're using a managed instance.

#### If we are getting large uploads very frequently

We need to optimize system latency. Currently, we're bottlenecked by the speed
we can do database operations. There's a couple of strategies here:

1. Make the DB computer bigger and faster, expensive but might be cheaper than paid programmer hours
2. Eventqueue/stream architecture. If a lot of people are wanting to upload files
they can send tasks into a queue managed by a system like NATS. NATS can load balance
the file processing task to worker nodes, which individually work to update the database.
This will likely not decrease latency, but it will ensure that all files do get processed.
3. If our dataset is soaring into the terabytes, it might be time for a managed Apache Spark solution.

## Integrating with other systems

This project is based around `FastAPI` which provides excellent facilities for generating `OpenAPI` compatible JSON files from endpoints.
This JSON can be used to generate client stub code for use by other services. 
