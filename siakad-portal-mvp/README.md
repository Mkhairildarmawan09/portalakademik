# SIAKAD Portal MVP — Portal Akademik Mahasiswa Berbasis Web

Proyek Mata Kuliah **Manajemen Proyek TI (MPTI)** dengan metodologi **Agile Scrum** (3 Anggota).
Antarmuka web disusun mengikuti spesifikasi **Figma Design System SIAKAD Portal MVP** (Font Inter, permukaan putih `#FFFFFF`, latar `#F4F6F9`, aksen `#0D6EFD`, `#198754`, `#FFC107`, `#DC3545`).

## Struktur File Proyek
```text
siakad-portal-mvp/
├── app.py                          # Controller utama Flask (Auth, Admin CRUD, KRS, Presensi, Nilai)
├── database.py                     # Skema SQLite (users, matakuliah, krs, attendance_logs, grades) & Seed Data
├── requirements.txt                # Daftar pustaka Python (Flask 3.0.3, Werkzeug 3.0.3)
├── PANDUAN_COMMIT_SPRINT_1_2.md    # Panduan langkah demi langkah commit Git Sprint 1 & 2 untuk 3 anggota
├── static/
│   └── css/
│       └── style.css               # Stylesheet sesuai Figma Style Guide (1440px, rasio 400:888px, pulse badge)
└── templates/
    ├── base.html                   # Kerangka dasar & Navbar 88px (SIAKAD PORTAL MVP)
    ├── login.html                  # 1. Halaman Login (Kertas akademik petak 48px + Card Login + Akun Demo)
    ├── dashboard_admin.html        # 2. Dashboard Admin (Tambah/Edit MK 400px & Tabel Master MK 888px)
    ├── dashboard_mahasiswa.html    # 3. Dashboard Mahasiswa (Pengajuan KRS & Status KRS/Presensi/KHS)
    └── dashboard_dosen.html        # 4. Dashboard Dosen (Kontrol Presensi Real-Time & Validasi KRS/Nilai)
```

## Cara Menjalankan di VS Code (Windows)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```
Buka browser ke `http://127.0.0.1:5000`.
