**Video presentasi YouTube (Unlisted):** `[ISI TAUTAN VIDEO SETELAH VIDEO DIUNGGAH]`

# Cafe Sedap Nikmat - UTS Komputasi Paralel dan Terdistribusi

API pemesanan sederhana untuk Cafe Sedap Nikmat. Proyek ini menggunakan FastAPI, SQLite melalui aiosqlite, BackgroundTasks, dan asyncio.Lock.

> Sebelum dikumpulkan, ganti placeholder tautan video, nama/NIM pada laporan, dan isi tabel benchmark dengan hasil pengujian asli dari komputer sendiri.

## 1. Fitur

- CRUD produk pada endpoint `/resource`.
- Transaksi pada endpoint `/transactions` dengan status `pending -> processing -> completed`.
- Proses lanjutan transaksi berjalan menggunakan FastAPI `BackgroundTasks` dan simulasi `await asyncio.sleep(3)`.
- Pengurangan stok dilindungi `asyncio.Lock` dalam satu proses/worker.
- Mode demonstrasi race condition tanpa lock melalui environment variable `ENABLE_STOCK_LOCK=0`.
- Database SQLite diakses secara asynchronous menggunakan aiosqlite.
- Seed 10 produk awal.
- Pengujian konkurensi menggunakan `test_race.py` dan benchmark menggunakan Locust.

## 2. Struktur folder

```text
project/
|-- main.py
|-- database.py
|-- models.py
|-- routes/
|   |-- __init__.py
|   |-- resource.py
|   `-- transaction.py
|-- seed.py
|-- test_race.py
|-- locustfile.py
|-- requirements.txt
|-- README.md
|-- docs/
|   |-- laporan_uts.docx
|   `-- laporan_uts.pdf
`-- results/
```

## 3. Instalasi pada Windows

Buka Command Prompt atau PowerShell, lalu masuk ke folder hasil ekstrak ZIP ini.

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python seed.py
```

Jika perintah `python` tidak dikenali, coba gunakan `py` sebagai pengganti `python`.

## 4. Menjalankan API

Jalankan satu worker terlebih dahulu untuk pengujian CRUD, transaksi, dan race condition:

```bat
uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1
```

Buka dokumentasi interaktif FastAPI pada browser:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/`

Biarkan terminal server tetap berjalan. Untuk menghentikan server tekan `Ctrl+C`.

## 5. Pengujian CRUD

Gunakan Swagger UI di `/docs`.

### POST `/resource`

Contoh JSON:

```json
{
  "nama": "Es Kopi Gula Aren",
  "kategori": "Kopi",
  "harga": 22000,
  "stok": 25,
  "deskripsi": "Es kopi dengan gula aren"
}
```

Uji juga:

- `GET /resource?skip=0&limit=10`
- `GET /resource/1`
- `PUT /resource/1` dengan JSON misalnya `{"stok": 30}`
- `DELETE /resource/ID` untuk menghapus permanen produk berdasarkan ID.

## 6. Pengujian transaksi BackgroundTasks

Kirim `POST /transactions` dengan JSON:

```json
{
  "product_id": 1,
  "qty": 1
}
```

Endpoint mengembalikan HTTP 202 dan status `pending` tanpa menunggu simulasi tiga detik. Setelah itu:

1. Buka `GET /transactions/{id}`.
2. Status akan bergerak dari `pending` ke `processing`, lalu `completed`.
3. `GET /transactions?status=pending` dapat digunakan untuk memfilter transaksi pending.

Karena proses latar belakang berlangsung cepat, gunakan pengulangan GET atau refresh Swagger beberapa kali untuk melihat perubahan status.

## 7. B3 - Race condition (jalankan dengan satu worker)

Pengujian ini mengatur stok produk ID 1 menjadi 1 secara otomatis. Tutup server sebelumnya dengan `Ctrl+C` sebelum mengganti mode.

### Tahap 1: tanpa Lock

Pada PowerShell:

```powershell
$env:ENABLE_STOCK_LOCK="0"
uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1
```

Buka terminal kedua, aktifkan virtual environment, lalu jalankan:

```powershell
python test_race.py
```

Hasil yang diharapkan: dua request mendapat HTTP 202, dan stok akhir menjadi -1. Ambil screenshot terminal kedua.

### Tahap 2: dengan Lock

Hentikan server. Pada PowerShell:

```powershell
$env:ENABLE_STOCK_LOCK="1"
uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1
```

Dari terminal kedua jalankan kembali:

```powershell
python test_race.py
```

Hasil yang diharapkan: satu request mendapat HTTP 202 dan satu request mendapat HTTP 409 Conflict. Stok akhir menjadi 0. Ambil screenshot terminal kedua.

> Catatan teknis: `asyncio.Lock` hanya melindungi coroutine dalam satu proses Python. Lock ini tidak dibagi antarproses Uvicorn worker. Karena itu pengujian B3 dilakukan dengan satu worker seperti instruksi. Sistem produksi multi-worker memerlukan pengamanan lintas-proses seperti transaksi database/atomic conditional UPDATE atau distributed lock.

## 8. C1 - Benchmark Locust (1 worker vs 4 worker)

Lakukan empat pengujian terpisah. Sebelum skenario write, pastikan stok produk ID 1 cukup besar, misalnya melalui `PUT /resource/1` dengan `{"stok": 1000}`.

### A. Read - 1 worker

Terminal server:

```bat
uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1
```

Terminal pengujian (PowerShell):

```powershell
$env:SCENARIO="read"
$env:TOTAL_REQUESTS="100"
$env:RUN_LABEL="read_1worker"
locust -f locustfile.py --headless -H http://127.0.0.1:8000 -u 20 -r 20 --run-time 2m --csv results/read_1worker
```

### B. Read - 4 worker

Hentikan server, lalu jalankan:

```bat
uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
```

Jalankan kembali perintah Locust Read di atas, ubah `RUN_LABEL` menjadi `read_4worker`, dan ubah nama file CSV menjadi `results/read_4worker`.

### C. Write - 1 worker dan D. Write - 4 worker

Gunakan server dengan jumlah worker yang sesuai. Pada terminal pengujian:

```powershell
$env:SCENARIO="write"
$env:TOTAL_REQUESTS="50"
$env:PRODUCT_ID="1"
$env:RUN_LABEL="write_1worker"
locust -f locustfile.py --headless -H http://127.0.0.1:8000 -u 10 -r 10 --run-time 2m --csv results/write_1worker
```

Untuk 4 worker, ganti `RUN_LABEL` menjadi `write_4worker`, nama output menjadi `results/write_4worker`, dan jalankan server dengan `--workers 4`.

Catat hasil Locust: jumlah request, total waktu (dicatat otomatis ke `results/benchmark_durations.csv`), throughput (request/detik), dan average response time. Simpan hasil CSV pada folder `results/`. Skenario Locust pada file ini membatasi jumlah request sesuai target 100 GET atau 50 POST.

## 9. Rumus analisis benchmark

- **Throughput** = jumlah request berhasil / total waktu pengujian (request per detik).
- **Rata-rata latensi** = nilai Average Response Time dari ringkasan Locust (milidetik).
- Bandingkan setiap skenario pada 1 worker dan 4 worker. Jangan menyimpulkan 4 worker selalu lebih cepat; SQLite dapat menjadi titik kontensi pada operasi tulis.

Isi tabel di `docs/laporan_uts.docx` dan perbarui PDF berdasarkan hasil yang benar-benar diperoleh.

## 10. Video presentasi (5-10 menit)

1. Perkenalan: nama, NIM, tema aplikasi, target pengguna.
2. Arsitektur: jelaskan FastAPI, SQLite/aiosqlite, BackgroundTasks, dan asyncio.Lock.
3. Demo Swagger: CRUD produk; POST transaksi lalu pantau statusnya hingga completed.
4. Demo race condition: tampilkan hasil tanpa lock dan dengan lock dari terminal.
5. Hasil benchmark: tampilkan tabel hasil 1 worker dibandingkan 4 worker.
6. Kesimpulan.

Wajah presenter wajib terlihat minimal pada pembukaan. Unggah video ke YouTube dengan visibilitas **Unlisted**, lalu tempelkan tautan video pada baris pertama README ini.

## 11. Catatan batasan

- Aplikasi ini merupakan fondasi demonstrasi pembelajaran, bukan sistem kasir produksi.
- `asyncio.Lock` bersifat lokal pada satu proses. Untuk deployment multi-worker, gunakan mekanisme atomik atau lock yang dikelola lintas-proses.
- Mode tanpa lock sengaja dibuat tidak aman untuk memperlihatkan race condition. Jangan digunakan untuk transaksi nyata.

## 12. GitHub

Buat repositori GitHub dengan status **Public**, lalu unggah seluruh folder proyek (termasuk `requirements.txt`, `README.md`, `locustfile.py`, `seed.py`, dan `docs/laporan_uts.pdf`). Lakukan commit yang benar-benar mencerminkan tahap kerja, misalnya:

1. `init: buat struktur proyek FastAPI`
2. `feat: tambah CRUD produk dengan aiosqlite`
3. `feat: tambah transaksi BackgroundTasks`
4. `feat: tambah pengamanan stok asyncio Lock dan race test`
5. `test: tambah skenario Locust dan dokumentasi benchmark`
6. `docs: lengkapi laporan dan panduan penggunaan`

## 13. Video Presentasi UTS

[Tonton Video Presentasi Cafe Sedap Nikmat](https://youtu.be/pTTTbVW24bM)

Jangan membuat commit palsu atau mengubah tanggal commit. Simpan tautan repositori dan tautan video pada catatan pengumpulan.
