"""Mengisi database dengan minimal 10 produk awal."""
import asyncio

import aiosqlite

from database import DB_PATH, init_db

PRODUCTS = [
    ("Kopi Susu Butter", "Kopi", 27000, 100, "Kopi susu creamy dengan butter"),
    ("Kopi Hitam", "Kopi", 16000, 100, "Kopi hitam klasik"),
    ("Markisa Melon", "Minuman", 19000, 100, "Minuman segar markisa dan melon"),
    ("Kopi Hitam Butter", "Kopi", 20000, 100, "Kopi hitam dengan butter"),
    ("Nasi Telur", "Makanan", 19000, 100, "Nasi dengan telur"),
    ("Roti Bakar Telur", "Makanan", 13000, 100, "Roti bakar isi telur"),
    ("Roti Sedap Keju Susu", "Makanan", 19000, 100, "Roti keju dan susu"),
    ("Pisang Goreng", "Camilan", 5000, 100, "Pisang goreng hangat"),
    ("Es Teh Manis", "Minuman", 7000, 100, "Teh manis dingin"),
    ("Cokelat Panas", "Minuman", 18000, 100, "Minuman cokelat hangat"),
]


async def main() -> None:
    await init_db()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM products")
        count = (await cursor.fetchone())[0]
        if count == 0:
            await db.executemany(
                "INSERT INTO products (nama, kategori, harga, stok, deskripsi) VALUES (?, ?, ?, ?, ?)",
                PRODUCTS,
            )
            await db.commit()
            print(f"Berhasil memasukkan {len(PRODUCTS)} produk awal.")
        else:
            print(f"Database sudah berisi {count} produk. Seed tidak menambahkan duplikat.")


if __name__ == "__main__":
    asyncio.run(main())
