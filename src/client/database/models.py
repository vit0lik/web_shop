import datetime

from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column, validates
from sqlalchemy import ForeignKey, DateTime, UniqueConstraint


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    surname: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    login: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow
    )

    cart_items: Mapped[list["CartItem"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )

    @validates("email")
    def validate_email(self, key, email):
        if not email or "@" not in email:
            raise ValueError("Invalid email address")
        return email


class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    id_customer: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    id_product: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(default=1)
    added_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint("id_customer", "id_product", name="uq_customer_product"),
    )

    customer: Mapped["Customer"] = relationship(back_populates="cart_items")

    @validates("quantity")
    def validate_quantity(self, key, quantity):
        if quantity < 1:
            raise ValueError("Quantity must be at least 1")
        return quantity
