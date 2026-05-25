import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from client.routers.auth import router as auth_router
from client.routers.cart import router as cart_router
from client.database.setup import create_db_and_tables

app = FastAPI(title="Client Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth")
app.include_router(cart_router, prefix="/cart")


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/health/")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("client.main:app", host="0.0.0.0", port=8001, reload=True)