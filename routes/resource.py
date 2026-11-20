from fastapi import APIRouter, HTTPException, Query, status

import database as db
from models import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter(prefix="/resource", tags=["Resource - Produk"])


@router.get("", response_model=list[ProductResponse])
async def read_resources(
    skip: int = Query(default=0, ge=0), limit: int = Query(default=10, ge=1, le=100)
):
    """Menampilkan daftar produk dengan pagination."""
    return await db.list_products(skip=skip, limit=limit)


@router.get("/{product_id}", response_model=ProductResponse)
async def read_resource(product_id: int):
    product = await db.get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    return product


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(data: ProductCreate):
    return await db.create_product(data.model_dump())


@router.put("/{product_id}", response_model=ProductResponse)
async def update_resource(product_id: int, data: ProductUpdate):
    existing = await db.get_product(product_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    updated = await db.update_product(product_id, data.model_dump(exclude_unset=True, exclude_none=True))
    return updated


@router.delete("/{product_id}")
async def delete_resource(product_id: int):
    deleted = await db.delete_product(product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    return {"message": "Produk berhasil dihapus permanen", "id": product_id}
