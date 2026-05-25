from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.database.models import Product
from client.database.queries import CartQueries, CustomerQueries
from client.database.setup import create_session
from client.routers.auth import get_current_customer
from client.schemas import (
    CartItemSchema,
    CartItemCreateSchema,
    CartItemUpdateSchema,
    CustomerPublicSchema,
)

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("/", response_model=list[CartItemSchema])
def get_cart(
    current_customer: CustomerPublicSchema = Depends(get_current_customer),
    session: Session = Depends(create_session),
):
    cart_items = CartQueries.get_cart(current_customer.id, session)
    return [CartItemSchema.model_validate(item) for item in cart_items]


@router.post("/items/", response_model=CartItemSchema)
def add_to_cart(
    item_data: CartItemCreateSchema,
    current_customer: CustomerPublicSchema = Depends(get_current_customer),
    session: Session = Depends(create_session),
):
    product = session.get(Product, item_data.product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    if product.quantity_at_storage < item_data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough stock",
        )

    cart_item = CartQueries.add_to_cart(
        customer_id=current_customer.id,
        product_id=item_data.product_id,
        quantity=item_data.quantity,
        session=session,
    )
    session.commit()

    return CartItemSchema.model_validate(cart_item)


@router.patch("/items/{cart_item_id}/", response_model=CartItemSchema)
def update_cart_item(
    cart_item_id: int,
    item_data: CartItemUpdateSchema,
    current_customer: CustomerPublicSchema = Depends(get_current_customer),
    session: Session = Depends(create_session),
):
    if item_data.quantity < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be at least 1",
        )

    cart_item = CartQueries.update_cart_item(
        cart_item_id=cart_item_id,
        customer_id=current_customer.id,
        quantity=item_data.quantity,
        session=session,
    )

    if cart_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found",
        )

    session.commit()
    return CartItemSchema.model_validate(cart_item)


@router.delete("/items/{cart_item_id}/")
def remove_from_cart(
    cart_item_id: int,
    current_customer: CustomerPublicSchema = Depends(get_current_customer),
    session: Session = Depends(create_session),
):
    success = CartQueries.remove_from_cart(
        cart_item_id=cart_item_id,
        customer_id=current_customer.id,
        session=session,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found",
        )

    session.commit()
    return {"message": "Item removed from cart"}


@router.delete("/")
def clear_cart(
    current_customer: CustomerPublicSchema = Depends(get_current_customer),
    session: Session = Depends(create_session),
):
    CartQueries.clear_cart(current_customer.id, session)
    session.commit()
    return {"message": "Cart cleared"}