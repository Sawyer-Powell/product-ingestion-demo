from datetime import datetime
from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy.orm import Mapped

class Base(DeclarativeBase):
    pass

class Product(Base):
    __tablename__: str = "products"

    code: Mapped[str] = mapped_column(String, primary_key=True)
    url: Mapped[str] = mapped_column(String)
    created_datetime: Mapped[datetime] = mapped_column(DateTime)
    last_modified_datetime: Mapped[datetime] = mapped_column(DateTime)
    product_name: Mapped[str | None] = mapped_column(String, nullable=True)
    brands: Mapped[str | None] = mapped_column(String, nullable=True)
    brands_tags: Mapped[str | None] = mapped_column(String, nullable=True)
    countries: Mapped[str | None] = mapped_column(String, nullable=True)
    countries_en: Mapped[str | None] = mapped_column(String, nullable=True)
    completeness: Mapped[float] = mapped_column(Float)
    image_nutrition_url: Mapped[str | None] = mapped_column(String, nullable=True)
    image_nutrition_small_url: Mapped[str | None] = mapped_column(String, nullable=True)
    energy_kcal_100g: Mapped[float | None] = mapped_column(Float, nullable=True)
    energy_100g: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat_100g: Mapped[float | None] = mapped_column(Float, nullable=True)
    saturated_fat_100g: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbohydrates_100g: Mapped[float | None] = mapped_column(Float, nullable=True)
    sugars_100g: Mapped[float | None] = mapped_column(Float, nullable=True)
    fiber_100g: Mapped[float | None] = mapped_column(Float, nullable=True)
    proteins_100g: Mapped[float | None] = mapped_column(Float, nullable=True)
