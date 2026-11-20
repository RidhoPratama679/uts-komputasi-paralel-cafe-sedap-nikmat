# Naskah Video Presentasi UTS - Cafe Sedap Nikmat

Durasi sasaran: sekitar 6-8 menit. Sesuaikan nama, NIM, hasil benchmark, dan tampilan aplikasi dengan hasil pengujian sendiri. Pastikan wajah terlihat saat pembukaan dan unggah video ke YouTube dengan status Unlisted.

## 1. Perkenalan (±30 detik)

"Assalamualaikum warahmatullahi wabarakatuh. Perkenalkan, nama saya [NAMA], NIM [NIM], dari Program Studi Teknik Informatika Universitas Muhammadiyah Pontianak. Pada UTS Komputasi Paralel dan Terdistribusi ini saya membuat aplikasi REST API Cafe Sedap Nikmat. Aplikasi ini ditujukan untuk membantu pengelolaan data produk dan transaksi pemesanan kafe."

## 2. Arsitektur aplikasi (±1-2 menit)

[Tampilkan gambar `arsitektur_cafe.png` atau diagram di laporan.]

"Aplikasi menggunakan FastAPI untuk menerima request HTTP. Data produk dan transaksi disimpan di SQLite, sedangkan akses database menggunakan aiosqlite supaya operasi database dapat dipanggil secara asynchronous. Model Pydantic digunakan untuk memvalidasi data yang dikirim oleh pengguna.

Ketika pengguna membuat transaksi, sistem memeriksa produk dan melakukan reservasi stok. Bagian pembacaan dan pengurangan stok dilindungi asyncio.Lock agar dua request dalam satu worker tidak mengambil stok terakhir pada saat yang sama. Setelah transaksi dibuat, status awalnya pending. FastAPI BackgroundTasks menjalankan proses lanjutan, mengubah status menjadi processing, menunggu tiga detik secara asynchronous, lalu mengubah status menjadi completed atau failed. Status dapat dipantau melalui endpoint GET transaksi."

## 3. Demo endpoint (±3 menit)

[Tampilkan `http://127.0.0.1:8000/docs`.]

"Pertama, saya mencoba GET /resource untuk melihat daftar produk. Berikutnya saya mencoba POST /resource untuk menambahkan produk. Setelah itu saya mencoba GET berdasarkan ID, PUT untuk memperbarui data, dan DELETE untuk menghapus produk.

Selanjutnya saya membuat transaksi melalui POST /transactions dengan product_id 1 dan qty 1. Response awal menunjukkan status pending. Saya mengambil ID transaksi tersebut lalu memantau dengan GET /transactions/{id}. Status berubah menjadi processing dan kemudian completed karena pemrosesan dijalankan oleh BackgroundTasks."

## 4. Demo race condition (±1-2 menit)

[Tampilkan terminal hasil `python test_race.py` pada mode tanpa lock dan dengan lock.]

"Pada tahap tanpa lock, saya mengatur stok produk ID 1 menjadi satu dan mengirim dua request transaksi secara bersamaan. Kedua request dapat membaca stok yang sama sebelum stok diperbarui, sehingga keduanya diterima dan stok akhir menjadi minus. Ini merupakan race condition yang menyebabkan overselling.

Setelah itu saya mengaktifkan asyncio.Lock dan mengulang pengujian dengan stok awal satu. Sekarang hanya satu transaksi yang diterima, sedangkan request kedua mendapat HTTP 409 Conflict karena stok sudah habis. Jadi, critical section yang dilindungi lock menjaga konsistensi stok selama pengujian satu worker."

## 5. Hasil benchmark (±1 menit)

[Tampilkan tabel benchmark yang sudah diisi hasil Locust.]

"Saya membandingkan server satu worker dan empat worker. Skenario read menggunakan 100 request GET dengan konkurensi 20, sedangkan skenario write menggunakan 50 request POST dengan konkurensi 10. Berdasarkan tabel, throughput dan rata-rata latensi pada satu worker adalah [ISI ANGKA], sedangkan pada empat worker adalah [ISI ANGKA]. Perbedaan ini menunjukkan [JELASKAN BERDASARKAN HASIL NYATA]. Pada skenario write, SQLite juga dapat menjadi titik kontensi karena penulisan data harus dikoordinasikan."

## 6. Kesimpulan (±30 detik)

"Kesimpulannya, aplikasi ini sudah menerapkan CRUD produk, transaksi asynchronous dengan BackgroundTasks, dan mekanisme asyncio.Lock untuk mencegah race condition pada satu worker. Pengujian Locust digunakan untuk membandingkan kinerja satu worker dan empat worker. Sekian presentasi dari saya. Terima kasih. Wassalamualaikum warahmatullahi wabarakatuh."
