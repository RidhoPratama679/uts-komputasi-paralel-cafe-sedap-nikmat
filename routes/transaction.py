"""Endpoint transaksi dan demonstrasi race condition pada stok."""
from __future__ import annotations

import asyncio
import os

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

import database as db
from models import TransactionCreate, TransactionResponse

router = APIRouter(prefix="/transactions", tags=["Transactions"])

# asyncio.Lock menjaga critical section pada satu proses/worker.
# Untuk demonstrasi race condition, jalankan server dengan ENABLE_STOCK_LOCK=0.
STOCK_LOCK_ENABLED = os.getenv("ENABLE_STOCK_LOCK", "1").strip().lower() not in {"0", "false", "no"}
stok_lock = asyncio.Lock()


async def potong_stok_tanpa_lock(item_id: int, qty: int) -> bool:
    """Versi tidak aman: dua request dapat membaca stok lama yang sama."""
    stok_terkini = await db.get_stok(item_id)
    if stok_terkini is None:
        return False
    # Jeda ini sengaja membuka kesempatan request lain masuk (race condition).
    await asyncio.sleep(0.01)
    if stok_terkini < qty:
        return False
    await db.decrement_stok(item_id, qty)
    return True


async def potong_stok_dengan_lock(item_id: int, qty: int) -> bool:
    """Versi aman dalam satu worker: baca, validasi, dan update dijaga lock."""
    async with stok_lock:
        stok_terkini = await db.get_stok(item_id)
        if stok_terkini is None:
            return False
        # Jeda tetap dipertahankan agar perbedaan lock terlihat saat pengujian.
        await asyncio.sleep(0.01)
        if stok_terkini < qty:
            return False
        await db.decrement_stok(item_id, qty)
        return True


async def reserve_stock(item_id: int, qty: int) -> bool:
    if STOCK_LOCK_ENABLED:
        return await potong_stok_dengan_lock(item_id, qty)
    return await potong_stok_tanpa_lock(item_id, qty)


async def proses_transaksi_background(trx_id: int) -> None:
    """Mengubah pending -> processing -> completed/failed di background."""
    try:
        await db.update_transaction_status(trx_id, "processing", "Pesanan sedang diproses")
        # Simulasi pekerjaan I/O secara asynchronous; request POST tidak menunggu ini.
        await asyncio.sleep(3)
        await db.update_transaction_status(trx_id, "completed", "Pesanan selesai diproses")
    except Exception as exc:  # noqa: BLE001 - status transaksi perlu ditandai gagal
        await db.update_transaction_status(trx_id, "failed", f"Pemrosesan gagal: {exc}")


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_transaction(data: TransactionCreate, background_tasks: BackgroundTasks):
    """Menerima transaksi dan mengembalikan status pending secara cepat.

    Pengurangan stok di sini merupakan reservasi stok. Pekerjaan lanjutan dijalankan
    BackgroundTasks, sehingga klien tidak menunggu simulasi proses selama 3 detik.
    """
    product = await db.get_product(data.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    # Kecukupan stok diverifikasi di dalam fungsi reservasi (termasuk di dalam lock).
    # Critical section B3: hanya satu transaksi boleh mengambil stok terakhir.
    reserved = await reserve_stock(data.product_id, data.qty)
    if not reserved:
        raise HTTPException(status_code=409, detail="Stok habis, transaksi ditolak")

    transaction = await db.create_transaction(
        product_id=data.product_id,
        product_name=product["nama"],
        qty=data.qty,
        price=float(product["harga"]),
        status="pending",
    )
    background_tasks.add_task(proses_transaksi_background, transaction["id"])
    return transaction


@router.get("", response_model=list[TransactionResponse])
async def read_transactions(status_filter: str | None = Query(default=None, alias="status")):
    allowed = {"pending", "processing", "completed", "failed"}
    if status_filter is not None and status_filter not in allowed:
        raise HTTPException(status_code=422, detail="Filter status tidak valid")
    return await db.list_transactions(status=status_filter)


@router.get("/{trx_id}", response_model=TransactionResponse)
async def read_transaction(trx_id: int):
    transaction = await db.get_transaction(trx_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
    return transaction
