# 📱 Money Tracker - Android Native App

Project aplikasi Android native resmi untuk **Money Tracker** (`https://moneytracker.mghazali.my.id`).

---

## 📁 Struktur Folder Project

```text
android/
├── app/
│   ├── build.gradle                             # Konfigurasi Gradle Module
│   ├── proguard-rules.pro                       # Obfuscation & Minification Rules
│   └── src/
│       └── main/
│           ├── AndroidManifest.xml              # Izin Internet, Download & Launcher
│           ├── java/id/my/mghazali/moneytracker/
│           │   └── MainActivity.java            # WebView Native Engine, SwipeRefresh & Sync
│           └── res/                             # Layout XML, Colors, Strings, Themes
├── build.gradle                                 # Root Gradle Build
├── settings.gradle                              # Project Settings
├── gradle.properties                            # JVM & AndroidX Settings
└── README.md
```

---

## 🚀 Fitur Aplikasi Android

1. **Full-Screen Mobile UI:** Tampilan responsif bebas address bar browser, terintegrasi ke status bar modern.
2. **Pull-to-Refresh:** Tarik ke bawah untuk refresh transaksi secara instan.
3. **Google Sign-In 1-Klik:** Sinkronisasi cookie dan token JWT OAuth 2.0 secara native.
4. **Download Manager:** Unduh laporan spreadsheet `.xlsx` langsung ke folder `Downloads` smartphone.
5. **Offline Fallback Detector:** Layar interaktif ramah pengguna ketika koneksi internet terputus.
6. **Smart Back Navigation:** Tombol 'Back' smartphone berpindah ke tab sebelumnya alih-alih langsung keluar aplikasi.

---

## 🛠 Cara Build APK di Android Studio

1. **Buka Project:**
   * Buka **Android Studio**.
   * Pilih **Open** $\rightarrow$ Arahkan ke folder: `c:\Users\mghaz\Project\Money Tracking\android`.
   * Tunggu Gradle Sync selesai.

2. **Generate APK Siap Pakai:**
   * Di menu atas Android Studio: Klik **Build** $\rightarrow$ **Build Bundle(s) / APK(s)** $\rightarrow$ **Build APK(s)**.
   * File `.apk` akan otomatis dibuat di folder: `android/app/build/outputs/apk/debug/app-debug.apk`.

3. **Install ke Smartphone:**
   * Salin file APK ke smartphone Android Anda via WhatsApp / Google Drive / USB Cable, lalu buka file untuk meng-install.
