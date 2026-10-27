from pydantic import BaseModel, Field


class Address(BaseModel):
    street: str = Field(min_length=1)
    city: str = Field(min_length=1)
    province: str = Field(min_length=1)
    postal_code: str = Field(min_length=1)
    country: str = Field(min_length=1)

class Customer(BaseModel):
    id: int
    name: str = Field(min_length=1)
    email: str = Field(min_length=1)
    address: Address = Field(...)
    status: bool = Field(...)

class CustomerCreate(BaseModel):

    name: str = Field(min_length=1)
    email: str = Field(min_length=1)
    address: Address = Field(...)
    street: str = Field(min_length=1)
    city: str = Field(min_length=1)
    province: str = Field(min_length=1)
    postal_code: str = Field(min_length=1)
    country: str = Field(min_length=1)
    status: bool = Field(...)

class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    email: str | None = Field(default=None, min_length=1)
    street: str | None = Field(default=None, min_length=1)
    city: str | None = Field(default=None, min_length=1)
    province: str | None = Field(default=None, min_length=1)
    postal_code: str | None = Field(default=None, min_length=1)
    country: str | None = Field(default=None, min_length=1)

