from pydantic import BaseModel, model_validator
from typing import Union, List


class Prices(BaseModel):
    Regular_Price: Union[float, str, int, None]
    Sale_Price: Union[float, str, int, None]
    Price_Per_Quantity: List[str]

    # @model_validator(mode="after")
    # def clean_price(self):
    #     # Ensure the price is clean
    #     self.Regular_Price = (
    #         text_cleaner(remove_dollar(self.Regular_Price))
    #         if self.Regular_Price
    #         else None
    #     )
    #
    #     self.Sale_Price = (
    #         text_cleaner(remove_dollar(self.Sale_Price))
    #         if self.Sale_Price
    #         else None
    #     )
    #
    #     self.Price_Per_Quantity = [
    #         x.replace("$", "") for x in self.Price_Per_Quantity
    #     ]
    #     return self


class Breadcrumb(BaseModel):
    Aisle: str | None
    Category: str | None
    Sub_Category: str | None

    @model_validator(mode="after")
    def clean_category(self):
        # Ensure the categories as capitalized
        self.Aisle = (
            self.Aisle.replace("-", " ").capitalize()
            if self.Aisle is not None
            else None
        )
        self.Category = (
            self.Category.replace("-", " ").capitalize()
            if self.Category
            else None
        )
        self.Sub_Category = (
            self.Sub_Category.replace("-", " ").capitalize()
            if self.Sub_Category
            else None
        )
        return self


class ProductModel(Prices, Breadcrumb):
    Name: str
    Sku: str
    Brand: str | None
    Size: str | None
    Size_Label: str | None
    Sale_Duration: str | None
    Image: str | None
    Url: str | None
    Store_id: int
    UPC: str | None
