from datetime import datetime
import io
from typing import BinaryIO
from fastapi import UploadFile
import ijson
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import CompoundSelect
from sqlmodel import Session, col, select, text
from app import db

import logging

logger = logging.getLogger(__name__)


class Product(BaseModel):
    code: str
    url: str
    created_datetime: datetime
    last_modified_datetime: datetime
    product_name: str
    brands: str | None = None
    brands_tags: str | None = None
    countries: str | None = None
    countries_en: str
    completeness: float
    image_nutrition_url: str | None = None
    image_nutrition_small_url: str | None = None
    energy_kcal_100g: float | None = Field(default=None, alias="energy-kcal_100g")
    energy_100g: float | None = None
    fat_100g: float | None = None
    saturated_fat_100g: float | None = Field(default=None, alias="saturated-fat_100g")
    carbohydrates_100g: float | None = None
    sugars_100g: float | None = None
    fiber_100g: float | None = None
    proteins_100g: float | None = None

    def to_db_type(self):
        return db.Product(
            id=self.code,
            url=self.url,
            created=self.created_datetime,
            last_modified=self.last_modified_datetime,
            name=self.product_name,
            brands=self.brands,
            countries=self.countries_en,
            image_nutrition_url=self.image_nutrition_url,
            energy_kcal_100g=self.energy_kcal_100g,
            energy_100g=self.energy_100g,
            fat_100g=self.fat_100g,
            saturated_fat_100g=self.saturated_fat_100g,
            carbohydrates_100g=self.carbohydrates_100g,
            sugars_100g=self.sugars_100g,
            fiber_100g=self.fiber_100g,
            proteins_100g=self.proteins_100g,
        )

    def get_countries(self) -> list[str]:
        """
        Tries to parse out a list of countries this product belongs to
        """
        return self.countries_en.split(",")


def transform_product(product: Product) -> Product | None:
    """
    Collection of cleanup actions done on product objects.
    Products can be filtered out from pipeline by returning None
    """
    # Filter out products with insufficient completeness
    if product.completeness < 0.25:
        logger.info(
            f"Product with code={product.code} omitted, did not satisfy completeness threshold at completeness={product.completeness}"
        )
        return None

    # Make all names lowercase and stripped
    product.product_name = product.product_name.lower().strip()

    # Make brands all lowercase and stripped
    if product.brands is not None:
        product.brands = product.brands.lower().strip()

    if product.brands_tags is not None:
        product.brands_tags = product.brands_tags.lower().strip()

    # Make countries all lowercase and stripped
    product.countries_en = product.countries_en.lower().strip()

    # Handling noise in countries_en
    product.countries_en = product.countries_en.replace("-en-", ",")
    product.countries_en = product.countries_en.replace("en-", "")

    return product


def parse_products(file_stream: BinaryIO):
    """
    Generates normalized and filtered Product objects from a file stream
    """
    for item in ijson.items(file_stream, "item"):
        try:
            # Gracefully handle no code
            if "code" not in item:
                logger.info(f"Item missing code, skipping {item}")
                continue

            # Gracefully handle blank product name
            if "product_name" not in item:
                logger.info(
                    f"Product with code={item['code']} missing product_name, skipping"
                )
                continue

            # Gracefully handle no english country tags
            if "countries_en" not in item:
                logger.info(
                    f"Product with code={item['code']} missing countries_en, skipping"
                )
                continue

            product = Product(**item)
            product = transform_product(product)
            if product is None:
                continue
            yield product
        except ValidationError as e:
            logger.warning(f"item JSON had an unexpected validation error - {e}")


def fast_pg_batch_upsert_prelude(session: Session):
    stmt = text("CREATE TEMP TABLE temp_product (LIKE product)")
    _ = session.execute(stmt)
    stmt = text("CREATE TEMP TABLE temp_producttocountry (LIKE producttocountry)")
    _ = session.execute(stmt)


def fast_pg_batch_upsert_postlude(session: Session):
    non_pk_product_cols = [f for f in db.Product.model_fields]
    print(non_pk_product_cols)
    non_pk_product_cols.remove("id")

    product_update_clause = ", ".join([
        f"{col} = excluded.{col}" for col in non_pk_product_cols
    ])

    _ = session.execute(
        text(f"""
        INSERT INTO product
        SELECT * FROM temp_product
        ON CONFLICT (id)
        DO UPDATE SET {product_update_clause};

        """)
    )

    _ = session.execute(
        text("""
        INSERT INTO producttocountry
        SELECT * FROM temp_producttocountry
        ON CONFLICT (product_id, country_id)
        DO NOTHING;
        """)
    )

    session.commit()

    session.execute(text(f"DROP TABLE IF EXISTS temp_product"))
    session.execute(text(f"DROP TABLE IF EXISTS temp_producttocountry"))

    session.commit()


def fast_pg_batch_upsert(
    session: Session, products: list[Product], countries: list[str]
):
    """
    This upsert strategy leverages special postgres facilities to
    stream our product data into the db.
    """

    product_buffer = io.StringIO()
    product_to_country_buffer = io.StringIO()

    for product in products:
        db_product = product.to_db_type()
        _ = product_buffer.write(db_product.as_pg_copyable() + "\n")

        if db_product.countries is None:
            continue

        for country in product.get_countries():
            db_country = db.Country(name=country)

            if country not in countries:
                session.add(db_country)
                countries.append(country)

            db_country.id = countries.index(country) + 1

            db_product_to_country = db.ProductToCountry(
                product_id=db_product.id, country_id=db_country.id
            )

            _ = product_to_country_buffer.write(
                db_product_to_country.as_pg_copyable() + "\n"
            )

    _ = product_buffer.seek(0)
    _ = product_to_country_buffer.seek(0)

    connection = session.connection().connection
    cursor = connection.cursor()

    cursor.copy_from(product_buffer, "temp_product")
    cursor.copy_from(product_to_country_buffer, "temp_producttocountry")


def get_countries(session: Session) -> list[str]:
    return [c.name for c in session.exec(select(db.Country)).all()]


def batch_upsert_products(
    session: Session, products: list[Product], countries: list[str]
):
    product_codes = [p.code for p in products]

    # Maintain maps to reduce db lookups for determing update vs. insert

    product_existence_map = {
        p.id: p
        for p in session.exec(
            select(db.Product).where(col(db.Product.id).in_(product_codes))
        ).all()
    }

    country_existence_map = {
        c.name: c
        for c in session.exec(
            select(db.Country).where(col(db.Country.name).in_(countries))
        ).all()
    }

    for product in products:
        p_countries = product.get_countries()
        db_product = product.to_db_type()

        # Upsert into the product table
        if db_product.id in product_existence_map:
            existing_db_product = product_existence_map[db_product.id]
            for k, v in db_product:
                setattr(existing_db_product, k, v)
            db_product = existing_db_product
        else:
            session.add(db_product)

        # Link country to product if relationship doesn't exist
        for country in p_countries:
            db_country = db.Country(name=country)

            if country in country_existence_map:
                db_country = country_existence_map[country]
            else:
                session.add(db_country)
                country_existence_map[country] = db_country

            stmt = select(db.ProductToCountry).filter_by(
                country_id=db_country.id, product_id=db_product.id
            )

            if session.exec(stmt).first() is None:
                session.add(
                    db.ProductToCountry(
                        country_id=db_country.id, product_id=db_product.id
                    )
                )

    session.commit()


DB_UPDATE_BATCH_SIZE = 1024  # larger batch sizes might help on a high latency network


def to_psql_db(session: Session, file_stream: UploadFile) -> int:
    """
    Postgres optimized version of to_db
    """
    product_buffer: list[Product] = []
    countries = get_countries(session)  # maintain an in memory unique list of countries
    i = 0

    fast_pg_batch_upsert_prelude(session)

    for i, product in enumerate(parse_products(file_stream.file)):
        product_buffer.append(product)

        if i % DB_UPDATE_BATCH_SIZE == 0:
            # batch_upsert_products(session, product_buffer, list(country_set))
            fast_pg_batch_upsert(session, product_buffer, countries)
            product_buffer = []

    # batch_upsert_products(session, product_buffer, list(country_set))
    fast_pg_batch_upsert(session, product_buffer, countries)

    fast_pg_batch_upsert_postlude(session)

    return i


def to_db(session: Session, file_stream: UploadFile) -> int:
    """
    Generic method to serialize openfoodproucts JSON into a
    SQL database.
    """
    product_buffer: list[Product] = []
    country_set: set[str] = set()
    i = 0

    for i, product in enumerate(parse_products(file_stream.file)):
        country_set.update(product.get_countries())
        product_buffer.append(product)

        if i % DB_UPDATE_BATCH_SIZE == 0:
            batch_upsert_products(session, product_buffer, list(country_set))
            product_buffer = []
            country_set = set()

    batch_upsert_products(session, product_buffer, list(country_set))
    return i
