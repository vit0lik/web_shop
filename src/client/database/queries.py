from sqlalchemy import select, Sequence, and_, or_, asc, desc
from api.database.models import Product, Category, Receipt, Sale
from client.database.models import Customer, CartItem
from sqlalchemy.orm import Session, joinedload
from datetime import datetime


class CustomerQueries:

    @staticmethod
    def insert_customer(
        name: str,
        surname: str,
        email: str,
        login: str,
        password_hash: str,
        session: Session,
    ) -> Customer:
        customer = Customer(
            name=name,
            surname=surname,
            email=email,
            login=login,
            password=password_hash,
        )
        session.add(customer)
        session.flush()
        return customer

    @staticmethod
    def customer_by_login(login: str, session: Session) -> Customer | None:
        query = select(Customer).where(Customer.login == login)
        return session.execute(query).scalar_one_or_none()

    @staticmethod
    def customer_by_email(email: str, session: Session) -> Customer | None:
        query = select(Customer).where(Customer.email == email)
        return session.execute(query).scalar_one_or_none()

    @staticmethod
    def customer_by_id(customer_id: int, session: Session) -> Customer | None:
        return session.get(Customer, customer_id)


class CatalogQueries:

    @staticmethod
    def all_products(
        session: Session,
        category_id: int | None = None,
        min_price: int | None = None,
        max_price: int | None = None,
        search: str | None = None,
        sort_by: str = "name",
        sort_order: str = "asc",
    ) -> Sequence[Product]:
        query = select(Product).options(joinedload(Product.category))

        conditions = []
        if category_id is not None:
            conditions.append(Product.id_category == category_id)
        if min_price is not None:
            conditions.append(Product.price >= min_price)
        if max_price is not None:
            conditions.append(Product.price <= max_price)
        if search is not None:
            conditions.append(Product.name.ilike(f"%{search}%"))

        if conditions:
            query = query.where(and_(*conditions))

        sort_column = getattr(Product, sort_by, Product.name)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        return session.execute(query).scalars().all()

    @staticmethod
    def product_by_id(product_id: int, session: Session) -> Product | None:
        query = (
            select(Product)
            .where(Product.id == product_id)
            .options(joinedload(Product.category))
        )
        return session.execute(query).scalar_one_or_none()

    @staticmethod
    def all_categories(session: Session) -> Sequence[Category]:
        query = select(Category)
        return session.execute(query).scalars().all()


class CartQueries:

    @staticmethod
    def get_cart(customer_id: int, session: Session) -> Sequence[CartItem]:
        query = (
            select(CartItem)
            .where(CartItem.id_customer == customer_id)
            .options(joinedload(CartItem.customer))
        )
        return session.execute(query).scalars().all()

    @staticmethod
    def add_to_cart(
        customer_id: int, product_id: int, quantity: int, session: Session
    ) -> CartItem:
        existing = session.execute(
            select(CartItem).where(
                and_(
                    CartItem.id_customer == customer_id,
                    CartItem.id_product == product_id,
                )
            )
        ).scalar_one_or_none()

        if existing:
            existing.quantity += quantity
            session.flush()
            return existing

        item = CartItem(
            id_customer=customer_id,
            id_product=product_id,
            quantity=quantity,
        )
        session.add(item)
        session.flush()
        return item

    @staticmethod
    def update_cart_item(
        cart_item_id: int, customer_id: int, quantity: int, session: Session
    ) -> CartItem | None:
        item = session.execute(
            select(CartItem).where(
                and_(
                    CartItem.id == cart_item_id,
                    CartItem.id_customer == customer_id,
                )
            )
        ).scalar_one_or_none()

        if item is None:
            return None

        item.quantity = quantity
        session.flush()
        return item

    @staticmethod
    def remove_from_cart(
        cart_item_id: int, customer_id: int, session: Session
    ) -> bool:
        item = session.execute(
            select(CartItem).where(
                and_(
                    CartItem.id == cart_item_id,
                    CartItem.id_customer == customer_id,
                )
            )
        ).scalar_one_or_none()

        if item is None:
            return False

        session.delete(item)
        session.flush()
        return True

    @staticmethod
    def clear_cart(customer_id: int, session: Session) -> None:
        items = session.execute(
            select(CartItem).where(CartItem.id_customer == customer_id)
        ).scalars().all()
        for item in items:
            session.delete(item)
        session.flush()


class CheckoutQueries:

    @staticmethod
    def checkout(
        customer_id: int,
        employee_id: int,
        session: Session,
    ) -> Receipt | None:
        cart_items = session.execute(
            select(CartItem).where(CartItem.id_customer == customer_id)
        ).scalars().all()

        if not cart_items:
            return None

        receipt = Receipt(created_at=datetime.utcnow(), id_employee=employee_id)
        session.add(receipt)
        session.flush()

        for item in cart_items:
            product = session.get(Product, item.id_product)
            if product is None or product.quantity_at_storage < item.quantity:
                raise ValueError(
                    f"Not enough stock for product '{product.name if product else item.id_product}'"
                )

            product.quantity_at_storage -= item.quantity

            sale = Sale(
                id_receipt=receipt.id,
                id_product=item.id_product,
                quintity=item.quantity,
            )
            session.add(sale)

        for item in cart_items:
            session.delete(item)
        session.flush()

        return receipt
