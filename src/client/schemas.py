from __future__ import annotations
from pydantic import BaseModel, EmailStr
from datetime import datetime


class TokenSchema(BaseModel):
    access_token: str
    token_type: str

    model_config = {"from_attributes": True}


class CustomerCreateSchema(BaseModel):
    name: str
    surname: str
    email: str
    login: str
    password: str


class CustomerPublicSchema(BaseModel):
    id: int
    name: str
    surname: str
    email: str
    login: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomerLoginSchema(BaseModel):
    login: str
    password: str


class CartItemSchema(BaseModel):
    id: int
    id_customer: int
    id_product: int
    quantity: int
    added_at: datetime

    model_config = {"from_attributes": True}


class CartItemCreateSchema(BaseModel):
    product_id: int
    quantity: int = 1


class CartItemUpdateSchema(BaseModel):
    quantity: int


class CategorySchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class ProductSchema(BaseModel):
    id: int
    name: str
    price: int
    quantity_at_storage: int
    category: CategorySchema

    model_config = {"from_attributes": True}


class ProductListItemSchema(BaseModel):
    id: int
    name: str
    price: int
    quantity_at_storage: int
    category_id: int

    model_config = {"from_attributes": True}