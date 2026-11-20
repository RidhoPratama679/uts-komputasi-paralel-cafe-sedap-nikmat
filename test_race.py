"""Uji dua transaksi serentak; stok produk ID 1 diatur menjadi 1 terlebih dahulu."""
import asyncio
import httpx

BASE_URL = "http://127.0.0.1:8000"
PRODUCT_ID = 1


async def main() -> None:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
        # Reset stok agar kondisi pengujian selalu sama.
        reset = await client.put(f"/resource/{PRODUCT_ID}", json={"stok": 1})
        if reset.status_code != 200:
            raise RuntimeError(f"Gagal mengatur stok awal: {reset.status_code} {reset.text}")

        payload = {"product_id": PRODUCT_ID, "qty": 1}
        req1 = client.post("/transactions", json=payload)
        req2 = client.post("/transactions", json=payload)
        res1, res2 = await asyncio.gather(req1, req2)

        print("Respon Request 1:", res1.status_code, res1.json())
        print("Respon Request 2:", res2.status_code, res2.json())

        # Tunggu BackgroundTasks menyelesaikan status transaksi.
        await asyncio.sleep(3.5)
        product = await client.get(f"/resource/{PRODUCT_ID}")
        print("Stok akhir:", product.json().get("stok"))

        for response in (res1, res2):
            if response.status_code in (200, 202):
                trx_id = response.json().get("id")
                detail = await client.get(f"/transactions/{trx_id}")
                print(f"Status transaksi {trx_id}:", detail.json().get("status"))


if __name__ == "__main__":
    asyncio.run(main())
