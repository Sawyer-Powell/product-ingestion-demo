from datetime import datetime
from typing import BinaryIO
from fastapi import UploadFile
import ijson
from pydantic import BaseModel, Field
from sqlmodel import Session, col, select
from app import db


class Product(BaseModel):
    code: str
    url: str
    created_datetime: datetime
    last_modified_datetime: datetime
    product_name: str | None = None
    brands: str | None = None
    brands_tags: str | None = None
    countries: str | None = None
    countries_en: str | None = None
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
            code = self.code,
            url = self.url,
            created_datetime = self.created_datetime,
            last_modified_datetime = self.last_modified_datetime,
            product_name = self.product_name,
            brands = self.brands,
            brands_tags = self.brands_tags,
            countries = self.countries,
            countries_en = self.countries_en,
            completeness = self.completeness,
            image_nutrition_url = self.image_nutrition_url,
            image_nutrition_small_url = self.image_nutrition_small_url,
            energy_kcal_100g = self.energy_kcal_100g,
            energy_100g = self.energy_100g,
            fat_100g = self.fat_100g,
            saturated_fat_100g = self.saturated_fat_100g,
            carbohydrates_100g = self.carbohydrates_100g,
            sugars_100g = self.sugars_100g,
            fiber_100g = self.fiber_100g,
            proteins_100g = self.proteins_100g,
        )


def from_json(file_stream: BinaryIO):
    """
    Generates Product objects from a file stream
    """
    for item in ijson.items(file_stream, 'item'):
        yield Product(**item)

def batch_upsert_products(session: Session, products: list[db.Product]):
    product_codes = [p.code for p in products]
    product_existence = {
        p.code: p for p in session.exec(
            select(db.Product).where(col(db.Product.code).in_(product_codes))
        ).all()
    }

    for product in products:
        if product.code in product_existence:
            db_product = product_existence[product.code]
            for k, v in product:
                setattr(db_product, k, v)
        else:
            session.add(product)

    session.commit()


DB_UPDATE_BATCH_SIZE = 64 # we update the database 64 products at a time from our data stream
def to_db(session: Session, file_stream: UploadFile, max: int | None = None):
    """
    Uses a Product generator to batch updates to the database.
    An optional field, max, is provided for debugging purposes on large files
    """
    product_buffer: list[db.Product] = []

    if max is None:
        for i, product in enumerate(from_json(file_stream.file)):
            db_product = product.to_db_type()
            product_buffer.append(db_product)

            if i % DB_UPDATE_BATCH_SIZE == 0:
                batch_upsert_products(session, product_buffer)
                product_buffer = []

        batch_upsert_products(session, product_buffer)

    else:
        for i, product in enumerate(from_json(file_stream.file)):
            db_product = product.to_db_type()
            product_buffer.append(db_product)

            if i > max - 1:
                batch_upsert_products(session, product_buffer)
                product_buffer = []
                break
