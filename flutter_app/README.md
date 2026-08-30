# 📱 Money Tracker Mobile (Flutter & Dart Native App)

Aplikasi Android **Real Native** (100% menggunakan bahasa pemrograman **Dart** dan framework **Flutter**) untuk **Money Tracker**.

---

## 🚀 Fitur Utama

- ⚡ **100% Native Render:** Performa tinggi (60–120 FPS) dengan Material Design 3.
- 🔐 **Multi-User Auth:** Sesi login tersimpan aman di perangkat (*SharedPreferences* / *Secure Storage*).
- 📊 **Dashboard Finansial:** Ringkasan pemasukan, pengeluaran, surplus/defisit bersih, dan saldo per dompet/rekening.
- 💸 **Pencatatan Transaksi:** Tambah transaksi instan (nominal, kategori, akun, keterangan) langsung tersimpan ke spreadsheet privat pengguna.
- 📈 **Portofolio Aset & Investasi:** Pantau nilai pasar saham, crypto, emas, modal masuk, dan floating PnL (+/- return %).
- 💳 **Cicilan & Hutang:** Pantau sisa tenor, sisa hutang, tanggal jatuh tempo, dan bayar cicilan 1-klik.
- 🤖 **Bot Telegram Pribadi:** Konfigurasi token bot dan whitelist User ID Telegram agar bot merespons chat transaksi otomatis 24/7.
- 📥 **Export Excel:** Sinkronisasi langsung dengan file Excel privat di server.

---

## 🛠️ Struktur Project

```text
flutter_app/
├── lib/
│   ├── main.dart                             # Entry point & theme setup
│   ├── config/
│   │   └── api_config.dart                   # URL backend https://moneytracker.mghazali.my.id
│   ├── models/
│   │   ├── transaction_model.dart            # Model Transaksi
│   │   ├── installment_model.dart            # Model Cicilan
│   │   ├── asset_model.dart                  # Model Aset & Investasi
│   │   └── summary_model.dart                # Model Ringkasan Finansial
│   ├── services/
│   │   ├── api_service.dart                  # REST Client (GET, POST, PUT, DELETE)
│   │   └── auth_service.dart                 # Token & Session Manager
│   └── screens/
│       ├── auth_screen.dart                  # Layar Login Multi-User
│       ├── main_navigation_screen.dart       # Bottom Navigation Bar
│       ├── dashboard_screen.dart             # Dashboard Ringkasan Finansial
│       ├── transactions_screen.dart          # Riwayat & Catat Transaksi
│       ├── assets_screen.dart                # Portofolio Saham, Crypto, Emas
│       ├── installments_screen.dart          # Cicilan & Bayar 1-Klik
│       └── settings_screen.dart              # Pengaturan Bot Telegram Pribadi
├── android/                                  # Native Android Engine (Kotlin / Gradle)
└── pubspec.yaml                              # Flutter Dependencies
```

---

## 📦 Cara Build APK Release

Jalankan perintah berikut di terminal:

```bash
cd flutter_app
flutter pub get
flutter build apk --release
```

File APK release akan tersedia di:
`flutter_app/build/app/outputs/flutter-apk/app-release.apk`
