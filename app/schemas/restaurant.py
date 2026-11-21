from pydantic import BaseModel, Field, model_validator


class RestaurantCreate(BaseModel):
    """Request body for creating a restaurant. The id is assigned by the server."""
    name: str = Field(min_length=1)
    rating: float = Field(ge=0, le=5)
    cuisine: str = Field(min_length=1)
    deliveryTime: int = Field(ge=0, description="Delivery time in minutes")


class Restaurant(BaseModel):
    id: int
    name: str = Field(min_length=1)
    rating: float = Field(ge=0, le=5)
    cuisine: str = Field(min_length=1)
    deliveryTime: int = Field(ge=0, description="Delivery time in minutes")


class RestaurantUpdate(BaseModel):
    """Partial update: omitted fields are left unchanged, but a provided field may not be null."""
    name: str | None = Field(default=None, min_length=1)
    rating: float | None = Field(default=None, ge=0, le=5)
    cuisine: str | None = Field(default=None, min_length=1)
    deliveryTime: int | None = Field(default=None, ge=0, description="Delivery time in minutes")

    @model_validator(mode="after")
    def provided_fields_must_not_be_null(self):
        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self
