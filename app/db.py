from datetime import datetime
import os
from typing import Annotated
from fastapi import Depends
from sqlalchemy import Engine, create_engine
from sqlmodel import Field, SQLModel, Session, inspect
import logging

logger = logging.getLogger(__name__)


class Product(SQLModel, table=True):
    id: str = Field(primary_key=True)
    url: str = Field()
    created: datetime = Field()
    last_modified: datetime = Field()
    name: str = Field()
    brands: str | None = Field(nullable=True)
    countries: str | None = Field(nullable=True)
    image_nutrition_url: str | None = Field(nullable=True)
    energy_kcal_100g: float | None = Field(nullable=True)
    energy_100g: float | None = Field(nullable=True)
    fat_100g: float | None = Field(nullable=True)
    saturated_fat_100g: float | None = Field(nullable=True)
    carbohydrates_100g: float | None = Field(nullable=True)
    sugars_100g: float | None = Field(nullable=True)
    fiber_100g: float | None = Field(nullable=True)
    proteins_100g: float | None = Field(nullable=True)

    def as_pg_copyable(self) -> str:
        """
        Converts this class into a string that can be
        copied directly into a postgres database
        """
        values = [getattr(self, field) for field in Product.model_fields]
        return "\t".join([str(v) if v is not None else "\\N" for v in values])


class Country(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field()

    def as_pg_copyable(self) -> str:
        """
        Converts this class into a string that can be
        copied directly into a postgres database
        """
        values = [getattr(self, field) for field in Country.model_fields]
        return "\t".join([str(v) if v is not None else "\\N" for v in values])


class ProductToCountry(SQLModel, table=True):
    product_id: str | None = Field(
        default=None, foreign_key="product.id", primary_key=True
    )
    country_id: int | None = Field(
        default=None, foreign_key="country.id", primary_key=True
    )

    def as_pg_copyable(self) -> str:
        """
        Converts this class into a string that can be
        copied directly into a postgres database
        """
        values = [getattr(self, field) for field in ProductToCountry.model_fields]
        return "\t".join([str(v) if v is not None else "\\N" for v in values])


connection_string = os.getenv("DATABASE_URL")

if connection_string is None:
    raise Exception("Environment variable DATABASE_URL is not set!")

def issqlite() -> bool:
    return connection_string is not None and "sqlite" in connection_string

def ispsql() -> bool:
    return connection_string is not None and "postgresql" in connection_string


connect_args = {}
if "sqlite" in connection_string:
    connect_args = {"check_same_thread": False}

engine = create_engine(connection_string, echo=False, connect_args=connect_args)


def ensure_tables_exist(engine: Engine):
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    model_tables = list(SQLModel.metadata.tables.keys())

    if not any(table in existing_tables for table in model_tables):
        SQLModel.metadata.create_all(engine)
        logger.info("Creating tables in db according to schema")


ensure_tables_exist(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
