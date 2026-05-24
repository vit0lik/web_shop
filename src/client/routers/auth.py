from fastapi import APIRouter, Depends, HTTPException, Form, status
from sqlalchemy.orm import Session

from api.utils.jwt import hash_pw, check_pw, encode_jwt, decode_jwt
from client.database.queries import CustomerQueries
from client.database.setup import create_session
from client.schemas import (
    CustomerCreateSchema,
    CustomerPublicSchema,
    CustomerLoginSchema,
    TokenSchema,
)
from client.config import settings
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/auth", tags=["auth"])
http_bearer = HTTPBearer()


def get_current_customer(
    creds: HTTPAuthorizationCredentials = Depends(http_bearer),
    session: Session = Depends(create_session),
) -> CustomerPublicSchema:
    token = creds.credentials
    try:
        token_data = decode_jwt(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    customer_id = token_data.get("customer_id")
    if customer_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    customer = CustomerQueries.customer_by_id(customer_id, session)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Customer not found",
        )

    return CustomerPublicSchema.model_validate(customer)


@router.post("/register/", response_model=CustomerPublicSchema)
def register_customer(
    name: str = Form(),
    surname: str = Form(),
    email: str = Form(),
    login: str = Form(),
    password: str = Form(),
    session: Session = Depends(create_session),
):
    existing_login = CustomerQueries.customer_by_login(login, session)
    if existing_login:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Login already taken",
        )

    existing_email = CustomerQueries.customer_by_email(email, session)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    password_hash = hash_pw(password)
    customer = CustomerQueries.insert_customer(
        name=name,
        surname=surname,
        email=email,
        login=login,
        password_hash=password_hash,
        session=session,
    )
    session.commit()

    return CustomerPublicSchema.model_validate(customer)


@router.post("/login/", response_model=TokenSchema)
def login_customer(
    login: str = Form(),
    password: str = Form(),
    session: Session = Depends(create_session),
):
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid login or password",
    )

    customer = CustomerQueries.customer_by_login(login, session)
    if customer is None:
        raise exc

    if not check_pw(password, customer.password):
        raise exc

    jwt_payload = {
        "customer_id": customer.id,
        "name": customer.name,
        "surname": customer.surname,
        "login": customer.login,
    }

    access_token = encode_jwt(jwt_payload)
    return TokenSchema(access_token=access_token, token_type="Bearer")


@router.get("/me/", response_model=CustomerPublicSchema)
def get_me(
    current_customer: CustomerPublicSchema = Depends(get_current_customer),
):
    return current_customer