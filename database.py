"""Akses SQLite secara asynchronous menggunakan aiosqlite."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import aiosqlite

DB_PATH = os.getenv("CAFE_DB_PATH", "cafe.db")


@asynccontextmanager
async def get_db() -> AsyncIterator[aiosqlite.Connection]:
    """Membuka koneksi singkat untuk setiap operasi database."""
    db = await aiosqlite.connect(DB_PATH, timeout=30)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    try:
        yield db
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    finally:
        await db.close()


async def init_db() -> None:
    async with get_db() as db:
        await db.execute(
            """CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama TEXT NOT NULL,
                kategori TEXT NOT NULL,
                harga REAL NOT NULL,
                stok INTEGER NOT NULL,
                deskripsi TEXT NOT NULL DEFAULT ''
            )"""
        )
        await db.execute(
            """CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                qty INTEGER NOT NULL,
                total REAL NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                message TEXT NOT NULL DEFAULT ''
            )"""
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status)"
        )


def _product_dict(row: aiosqlite.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def _transaction_dict(row: aiosqlite.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


async def create_product(data: dict[str, Any]) -> dict[str, Any]:
    async with get_db() as db:
        cursor = await db.execute(
            "INSERT INTO products (nama, kategori, harga, stok, deskripsi) VALUES (?, ?, ?, ?, ?)",
            (data["nama"], data["kategori"], data["harga"], data["stok"], data["deskripsi"]),
        )
        product_id = cursor.lastrowid
        cursor = await db.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        return _product_dict(await cursor.fetchone())  # type: ignore[return-value]


async def list_products(skip: int = 0, limit: int = 10) -> list[dict[str, Any]]:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM products ORDER BY id LIMIT ? OFFSET ?", (limit, skip)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_product(product_id: int) -> dict[str, Any] | None:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        return _product_dict(await cursor.fetchone())


async def update_product(product_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
    if not data:
        return await get_product(product_id)
    allowed = {"nama", "kategori", "harga", "stok", "deskripsi"}
    fields = [(key, value) for key, value in data.items() if key in allowed]
    if not fields:
        return await get_product(product_id)
    assignments = ", ".join(f"{key} = ?" for key, _ in fields)
    values = [value for _, value in fields]
    async with get_db() as db:
        await db.execute(
            f"UPDATE products SET {assignments} WHERE id = ?", (*values, product_id)
        )
        cursor = await db.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        return _product_dict(await cursor.fetchone())


async def delete_product(product_id: int) -> bool:
    async with get_db() as db:
        cursor = await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        return cursor.rowcount > 0


async def get_stok(product_id: int) -> int | None:
    async with get_db() as db:
        cursor = await db.execute("SELECT stok FROM products WHERE id = ?", (product_id,))
        row = await cursor.fetchone()
        return int(row["stok"]) if row is not None else None


async def decrement_stok(product_id: int, qty: int) -> None:
    """Mengurangi stok tanpa kondisi WHERE stok >= qty (untuk demo race condition)."""
    async with get_db() as db:
        await db.execute(
            "UPDATE products SET stok = stok - ? WHERE id = ?", (qty, product_id)
        )


async def create_transaction(
    product_id: int, product_name: str, qty: int, price: float, status: str = "pending"
) -> dict[str, Any]:
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    async with get_db() as db:
        cursor = await db.execute(
            """INSERT INTO transactions
               (product_id, product_name, qty, total, status, created_at, updated_at, message)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (product_id, product_name, qty, qty * price, status, now, now, "Transaksi diterima"),
        )
        trx_id = cursor.lastrowid
        cursor = await db.execute("SELECT * FROM transactions WHERE id = ?", (trx_id,))
        return _transaction_dict(await cursor.fetchone())  # type: ignore[return-value]


async def update_transaction_status(
    trx_id: int, status: str, message: str = ""
) -> dict[str, Any] | None:
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    async with get_db() as db:
        await db.execute(
            "UPDATE transactions SET status = ?, updated_at = ?, message = ? WHERE id = ?",
            (status, now, message, trx_id),
        )
        cursor = await db.execute("SELECT * FROM transactions WHERE id = ?", (trx_id,))
        return _transaction_dict(await cursor.fetchone())


async def list_transactions(status: str | None = None) -> list[dict[str, Any]]:
    async with get_db() as db:
        if status:
            cursor = await db.execute(
                "SELECT * FROM transactions WHERE status = ? ORDER BY id DESC", (status,)
            )
        else:
            cursor = await db.execute("SELECT * FROM transactions ORDER BY id DESC")
        return [dict(row) for row in await cursor.fetchall()]


async def get_transaction(trx_id: int) -> dict[str, Any] | None:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM transactions WHERE id = ?", (trx_id,))
        return _transaction_dict(await cursor.fetchone())
