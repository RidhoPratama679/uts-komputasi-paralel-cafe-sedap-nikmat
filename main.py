from contextlib import asynccontextmanager

from fastapi import FastAPI

import database
from routes.resource import router as resource_router
from routes.transaction import router as transaction_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.init_db()
    yield


app = FastAPI(
    title="Cafe Sedap Nikmat API",
    description="REST API pemesanan kafe untuk UTS Komputasi Paralel dan Terdistribusi.",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(resource_router)
app.include_router(transaction_router)


@app.get("/", tags=["Informasi"])
async def root():
    return {"message": "Selamat datang di Cafe Sedap Nikmat API", "docs": "/docs"}
