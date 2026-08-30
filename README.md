# 💰 Money Tracking App (Web Dashboard + Telegram Bot + Excel Sync)

Aplikasi pencatatan keuangan pribadi untuk memonitor **Pemasukan**, **Pengeluaran**, dan **Cicilan/Hutang Bulanan** yang terintegrasi secara realtime dengan file **Microsoft Excel (`MoneyTracking.xlsx`)**.

---

## 🌟 Fitur Utama

1. **📊 Web Dashboard Modern & Interaktif**:
   - **Kartu Ringkasan KPI**: Total Saldo, Pemasukan Bulan Ini, Pengeluaran Bulan Ini, Beban Cicilan Berjalan, dan *Net Cashflow*.
   - **Grafik Donut**: Proporsi alokasi pengeluaran per kategori.
   - **Grafik Batang (*Bar Chart*)**: Tren arus kas bulanan (6 bulan terakhir).
   - **Filter Fleksibel**: Pilih bulan dan tahun, filter berdasarkan kategori, rekening/dompet, atau tipe transaksi.
   - **Tombol Ekspor**: Unduh file Excel terbaru kapan saja.

2. **💳 Pelacak Cicilan & Hutang (*Installment Manager*)**:
   - Catat pinjaman, tenor, sisa pokok, dan tanggal jatuh tempo.
   - *Progress Bar* pelunasan otomatis.
   - **Tombol 1-Klik Bayar Cicilan**: Otomatis memotong sisa tenor dan mencatat transaksi pengeluaran di Excel.

3. **🤖 Telegram Bot (Input Cepat via Smartphone)**:
   - Mencatat pengeluaran/pemasukan saat di jalan hanya dengan chat natural:
     - `keluar 35000 makan siang`
     - `keluar 150k bensin [Mandiri]`
     - `masuk 7.5jt gaji bulanan [BCA]`
   - Menu tombol interaktif untuk cek saldo, rekap bulanan, dan pelunasan cicilan.
   - Dilengkapi sistem keamanan (*Whitelist User ID*).

4. **📁 Excel Realtime Synchronization (`MoneyTracking.xlsx`)**:
   - Format sheet terstruktur rapi: `Transaksi`, `Cicilan`, `Master_Data`, dan `Ringkasan`.
   - Aman dari korupsi data (*Thread-safe lock* & rotasi backup otomatis di folder `/backups`).

---

## 🚀 Cara Menjalankan Aplikasi

### 1. Jalankan via Batch File (Windows)
Cukup klik ganda (double-click) file:
```
run.bat
```

### 2. Atau Jalankan via Terminal / CMD
```bash
python main.py
```

Setelah aplikasi berjalan, buka browser di:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## ⚙️ Panduan Setup Telegram Bot (Opsional)

Jika ingin mencatat transaksi via Telegram dari HP:

1. Buka Telegram dan cari **`@BotFather`**.
2. Ketik `/newbot`, lalu ikuti petunjuk untuk membuat bot dan salin **HTTP API Token** yang diberikan.
3. Cari **`@userinfobot`** di Telegram untuk melihat **User ID Telegram** Anda.
4. Buat file `.env` di folder project ini (atau salin dari `.env.example`), lalu isi:
   ```env
   TELEGRAM_BOT_TOKEN=1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ
   ALLOWED_TELEGRAM_USERS=123456789
   ```
5. Jalankan ulang aplikasi (`python main.py` atau `run.bat`).
6. Buka bot Telegram Anda dan ketik `/start`!

---

## 📂 Struktur File Project

```
Money Tracking/
├── MoneyTracking.xlsx     # File Excel database utama
├── main.py                # Entry point aplikasi (Web + Bot)
├── app.py                 # Backend REST API (FastAPI)
├── bot.py                 # Layanan Telegram Bot
├── excel_manager.py       # Engine sinkronisasi & manipulasi Excel
├── config.py              # Konfigurasi aplikasi
├── run.bat                # Skrip 1-klik untuk Windows
├── .env.example           # Contoh konfigurasi environment
├── templates/
│   └── index.html         # Tampilan Web UI Dashboard
├── static/
│   └── js/
│       └── app.js         # Logika interaktif frontend
└── backups/               # Folder backup otomatis file Excel
```
