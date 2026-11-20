"""Model Pydantic untuk validasi request dan response."""
from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    nama: str = Field(min_length=2, max_length=100)
    kategori: str = Field(min_length=2, max_length=60)
    harga: float = Field(gt=0)
    stok: int = Field(ge=0)
    deskripsi: str = Field(default="", max_length=300)


class ProductUpdate(BaseModel):
    nama: str | None = Field(default=None, min_length=2, max_length=100)
    kategori: str | None = Field(default=None, min_length=2, max_length=60)
    harga: float | None = Field(default=None, gt=0)
    stok: int | None = Field(default=None, ge=0)
    deskripsi: str | None = Field(default=None, max_length=300)


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nama: str
    kategori: str
    harga: float
    stok: int
    deskripsi: str


class TransactionCreate(BaseModel):
    product_id: int = Field(gt=0)
    qty: int = Field(gt=0, le=1000)


class TransactionResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    qty: int
    total: float
    status: str
    created_at: str
    updated_at: str
    message: str
