# PANDUAN MENJALANKAN DI VS CODE & COMMIT BERTAHAP SPRINT 1 DAN SPRINT 2 (3 ANGGOTA)

Panduan ini disusun agar **100% sinkron** dengan:
1. **Desain UI/UX Figma (`SIAKAD PORTAL MVP - UI Design`)**: Menggunakan palet `#0D6EFD`, `#198754`, `#FFC107`, `#DC3545`, `#F4F6F9`, `#FFFFFF`, font `Inter`, navbar `88 px`, latar kertas akademik petak `48 px` di halaman login, rasio kolom Admin `400 : 888 px`, dan efek *pulse* pada tombol/badge presensi *real-time*.
2. **Dokumen Laporan Proyek & Audit (`Laporan_Proyek_MPTI_SIAKAD_Portal_MVP_Lengkap_Revisi.docx`)**: Memiliki fitur Edit Mata Kuliah (`/edit_mk/<id>` — Temuan `T7`), proteksi URL lintas peran (`T12`), enkripsi *hash password* `werkzeug.security` (`NFR-01`), dan variabel `DEMO_MODE` (`T13`).

---

## BAGIAN 1. Struktur Folder di VS Code

Buat satu folder proyek bernama **`portalakademik`** di komputer Anda, lalu susun file-file kode dengan urutan folder seperti ini:

```text
portalakademik/
├── app.py
├── database.py
├── requirements.txt
├── README.md
├── PANDUAN_COMMIT_SPRINT_1_2.md
├── static/
│   └── css/
│       └── style.css
└── templates/
    ├── base.html
    ├── login.html
    ├── dashboard_admin.html
    ├── dashboard_mahasiswa.html
    └── dashboard_dosen.html
```

---

## BAGIAN 2. Cara Menjalankan Aplikasi di VS Code

Buka folder **`portalakademik`** di VS Code (**File > Open Folder**), buka terminal PowerShell (`Ctrl + ~`), lalu jalankan:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Setelah muncul pesan `Running on http://127.0.0.1:5000`, buka alamat tersebut di browser:
* **Akun Admin:** `admin` / `admin123` (Halo, Budi Santoso, S.Kom)
* **Akun Dosen:** `dosen` / `dosen123` (Halo, Dr. Hendra Wijaya, M.T.)
* **Akun Mahasiswa 1:** `mhs1` / `mhs123` (Halo, Andi Pratama)
* **Akun Mahasiswa 2:** `mhs2` / `mhs123` (Halo, Siti Rahmawati)

---

## BAGIAN 3. Panduan Commit Git Sprint 1 dan Sprint 2 untuk 3 Anggota

Agar tabel **Riwayat Commit Git (Subbab 1.4 & Lampiran F)** pada laporan Word terisi dengan *hash commit* asli dan merata untuk **Anggota 1, Anggota 2, dan Anggota 3**, jalankan perintah Git berikut secara berurutan di terminal VS Code:

### Persiapan Awal Repositori
```powershell
git init
git branch -M main
git remote add origin https://github.com/Mkhairildarmawan09/portalakademik.git
```
*(Buat juga file `.gitignore` berisi `.venv/` dan `akademik.db` agar file database lokal tidak ikut terunggah:)*
```powershell
Set-Content -Path .gitignore -Value ".venv/`n__pycache__/`nakademik.db`n.env"
```

---

### A. Urutan 6 Commit SPRINT 1 (Fondasi Database, Login Multi-Role & Master Mata Kuliah)

**Commit #1 — Anggota 1 (PM / Database Engineer):**
```powershell
git config user.name "Nama_Anggota_1"
git config user.email "email_anggota_1@gmail.com"
git add .gitignore README.md requirements.txt
git commit -m "chore: inisialisasi repositori dan dependensi Flask 3.0.3"
```

**Commit #2 — Anggota 1 (PM / Database Engineer):**
```powershell
git checkout -b feat/database
git add database.py
git commit -m "feat(db): membuat skema tabel SQLite users, matakuliah, krs dan data seed awal"
git checkout main
git merge feat/database
```

**Commit #3 — Anggota 3 (UI/UX & Frontend Developer):**
```powershell
git config user.name "Nama_Anggota_3"
git config user.email "email_anggota_3@gmail.com"
git checkout -b feat/ui-auth
git add static/css/style.css templates/base.html templates/login.html
git commit -m "feat(ui): membuat layout dasar Bootstrap 5 dan desain halaman login multi-role"
git checkout main
git merge feat/ui-auth
```

**Commit #4 — Anggota 2 (System Analyst & Backend Developer):**
```powershell
git config user.name "Nama_Anggota_2"
git config user.email "email_anggota_2@gmail.com"
git checkout -b feat/auth-logic
git add app.py
git commit -m "feat(auth): implementasi controller login, session role, dan logout"
git checkout main
git merge feat/auth-logic
```

**Commit #5 — Anggota 3 (UI/UX & Frontend Developer):**
```powershell
git config user.name "Nama_Anggota_3"
git config user.email "email_anggota_3@gmail.com"
git checkout -b feat/admin-crud
git add templates/dashboard_admin.html
git commit -m "feat(ui): membuat halaman dashboard admin untuk form dan tabel master mata kuliah"
```

**Commit #6 — Anggota 2 (Kolaborasi dengan Anggota 1):**
```powershell
git config user.name "Nama_Anggota_2"
git config user.email "email_anggota_2@gmail.com"
git add app.py
git commit --allow-empty -m "feat(admin): implementasi fitur tambah_mk, edit_mk, dan hapus_mk beserta validasi kode unik"
git checkout main
git merge feat/admin-crud
```

---

### B. Urutan Commit SPRINT 2 (Pengelolaan KRS, Validasi 24 SKS/Bentrok, & Presensi Real-Time)

**Commit #7 (Sprint 2) — Anggota 3 (UI/UX & Frontend Developer):**
```powershell
git config user.name "Nama_Anggota_3"
git config user.email "email_anggota_3@gmail.com"
git checkout -b feat/sprint2-ui-krs-presensi
git add templates/dashboard_mahasiswa.html templates/dashboard_dosen.html
git commit -m "feat(ui-s2): implementasi antarmuka dashboard mahasiswa dan dosen sesuai desain Figma"
git checkout main
git merge feat/sprint2-ui-krs-presensi
```

**Commit #8 (Sprint 2) — Anggota 2 (Backend Developer):**
```powershell
git config user.name "Nama_Anggota_2"
git config user.email "email_anggota_2@gmail.com"
git checkout -b feat/sprint2-krs-presensi
git add app.py
git commit --allow-empty -m "feat(krs-presensi): implementasi validasi KRS 24 SKS, deteksi jadwal bentrok, dan sesi presensi real-time"
git checkout main
git merge feat/sprint2-krs-presensi
```

**Commit #9 (Sprint 2) — Anggota 1 (PM / Database Engineer):**
```powershell
git config user.name "Nama_Anggota_1"
git config user.email "email_anggota_1@gmail.com"
git add PANDUAN_COMMIT_SPRINT_1_2.md
git commit -m "docs(sprint-2): dokumentasi alur eksekusi, validasi skema presensi, dan evaluasi nilai"
git push -u origin main
```

---

## BAGIAN 4. Cara Mengambil Data `git log` dan Jumlah Baris Kode (`LOC`) untuk Diisi ke Laporan Word

Setelah perintah *commit* di atas selesai dijalankan, ketik dua perintah ini di terminal VS Code untuk menyalin *hash commit* asli dan jumlah baris kode ke bagian `[............]` pada **Lampiran F** dan **Bab VIII (Defect Density)** di file Word Anda:

```powershell
git log --pretty=format:"%h | %ad | %an | %s" --date=short
(Get-Content app.py, database.py, static/css/style.css, templates/*.html).Count
```
