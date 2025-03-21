from datetime import datetime
from typing import BinaryIO
from fastapi import UploadFile
import ijson
from pydantic import BaseModel, Field, ValidationError
from sqlmodel import Session, col, select
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
                    f"Product with code {item['code']} missing product_name, skipping"
                )
                continue

            # Gracefully handle no english country tags
            if "countries_en" not in item:
                logger.info(
                    f"Product with code {item['code']} missing countries_en, skipping"
                )
                continue

            product = Product(**item)
            product = transform_product(product)
            if product is None:
                continue
            yield product
        except ValidationError as e:
            logger.warning(f"item JSON had an unexpected validation error - {e}")


def batch_upsert_products(
    session: Session, products: list[Product], countries: list[str]
):
    product_codes = [p.code for p in products]
    product_existence = {
        p.id: p
        for p in session.exec(
            select(db.Product).where(col(db.Product.id).in_(product_codes))
        ).all()
    }

    country_existence = {
        c.name: c
        for c in session.exec(
            select(db.Country).where(col(db.Country.name).in_(countries))
        ).all()
    }

    for product in products:
        p_countries = product.get_countries()
        db_product = product.to_db_type()

        # Upsert into the product table
        if db_product.id in product_existence:
            existing_db_product = product_existence[db_product.id]
            for k, v in db_product:
                setattr(existing_db_product, k, v)
            db_product = existing_db_product
        else:
            session.add(db_product)

        # Upsert into the country table
        # Link country to product if relationship doesn't exist
        for country in p_countries:
            db_country = db.Country(name=country)

            if country in country_existence:
                db_country = country_existence[country]
            else:
                session.add(db_country)
                country_existence[country] = db_country

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


DB_UPDATE_BATCH_SIZE = 512


def to_db(session: Session, file_stream: UploadFile):
    """
    Uses a Product generator to batch updates to the database.
    """
    product_buffer: list[Product] = []
    country_set: set[str] = set()

    for i, product in enumerate(parse_products(file_stream.file)):
        country_set.update(product.get_countries())
        product_buffer.append(product)

        if i % DB_UPDATE_BATCH_SIZE == 0:
            batch_upsert_products(session, product_buffer, list(country_set))
            product_buffer = []
            country_set = set()

    batch_upsert_products(session, product_buffer, list(country_set))
