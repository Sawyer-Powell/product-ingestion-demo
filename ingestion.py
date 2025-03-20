from datetime import datetime
import ijson
from pydantic import BaseModel, Field


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


async def products(json_stream):
    async for item in ijson.items_async(json_stream, 'item'):
        yield Product(**item)
