from datetime import datetime
import os
import sys
from typing import Annotated
from fastapi import Depends
from sqlalchemy import create_engine
from sqlmodel import Field, SQLModel, Session

class Product(SQLModel, table=True):
    code: str = Field(primary_key=True)
    url: str = Field()
    created_datetime: datetime = Field()
    last_modified_datetime: datetime = Field()
    product_name: str | None = Field(nullable=True)
    brands: str | None = Field(nullable=True)
    brands_tags: str | None = Field(nullable=True)
    countries: str | None = Field(nullable=True)
    countries_en: str | None = Field(nullable=True)
    completeness: float = Field()
    image_nutrition_url: str | None = Field(nullable=True)
    image_nutrition_small_url: str | None = Field(nullable=True)
    energy_kcal_100g: float | None = Field(nullable=True)
    energy_100g: float | None = Field(nullable=True)
    fat_100g: float | None = Field(nullable=True)
    saturated_fat_100g: float | None = Field(nullable=True)
    carbohydrates_100g: float | None = Field(nullable=True)
    sugars_100g: float | None = Field(nullable=True)
    fiber_100g: float | None = Field(nullable=True)
    proteins_100g: float | None = Field(nullable=True)

connection_string = os.getenv("DATABASE_URL")

if connection_string is None:
    raise Exception("Environment variable DATABASE_URL is not set!")

engine = create_engine(connection_string,echo=True)

def create_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
