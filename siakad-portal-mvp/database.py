"""
Modul Basis Data, Helper Validasi Jadwal/Token, & Seed Data Otomatis — SIAKAD Portal MVP
Sesuai Desain Figma & Perbaikan Audit (T5, T6, T7, T12, T13)
Menggunakan SQLite3 (akademik.db) dengan kata sandi ter-hash (werkzeug.security).
"""

import os
import re
import secrets
import sqlite3
import string
from datetime import datetime

try:
    from werkzeug.security import generate_password_hash, check_password_hash
except ImportError:
    import hashlib
    import hmac

    def generate_password_hash(password: str) -> str:
        salt = secrets.token_hex(8)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()
        return f"pbkdf2:sha256:100000${salt}${dk}"

    def check_password_hash(pwhash: str, password: str) -> bool:
        try:
            _, salt, dk = pwhash.split("$", 2)
            calc = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()
            return hmac.compare_digest(dk, calc)
        except Exception:
            return False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "akademik.db")

HARI_PATTERN = r"(senin|selasa|rabu|kamis|jumat|jum'at|sabtu|minggu)"
JAM_PATTERN = r"(\d{1,2})[:.](\d{2})\s*[-–—]\s*(\d{1,2})[:.](\d{2})"


def get_db_connection():
    """Membuka koneksi SQLite dengan Row factory agar kolom dapat diakses seperti dict."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def generate_token_presensi(length: int = 6) -> str:
    """Membangkitkan kode token presensi alfanumerik acak sepanjang 6 karakter (FR-11)."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def parse_jadwal(jadwal_str: str):
    """
    Mem-parsing string jadwal (mis. 'Senin, 08:00 - 10:30') menjadi tuple
    (hari_normalized, menit_mulai, menit_selesai). Mengembalikan None bila format tidak standar.
    """
    if not jadwal_str:
        return None
    teks = jadwal_str.strip().lower()
    hari_match = re.search(HARI_PATTERN, teks)
    jam_match = re.search(JAM_PATTERN, teks)
    if not hari_match or not jam_match:
        return None

    hari = hari_match.group(1).replace("'", "")
    jam_mulai = int(jam_match.group(1))
    menit_mulai = int(jam_match.group(2))
    jam_selesai = int(jam_match.group(3))
    menit_selesai = int(jam_match.group(4))

    total_mulai = jam_mulai * 60 + menit_mulai
    total_selesai = jam_selesai * 60 + menit_selesai
    if total_selesai <= total_mulai:
        return None
    return hari, total_mulai, total_selesai


def is_jadwal_bentrok(jadwal_a: str, jadwal_b: str) -> bool:
    """
    Mendeteksi bentrok jadwal berdasarkan kesamaan hari dan irisan rentang jam (FR-09 / TC-17).
    Jika salah satu jadwal tidak mengikuti format standar, gunakan perbandingan teks langsung.
    """
    parsed_a = parse_jadwal(jadwal_a)
    parsed_b = parse_jadwal(jadwal_b)
    if parsed_a and parsed_b:
        hari_a, start_a, end_a = parsed_a
        hari_b, start_b, end_b = parsed_b
        return hari_a == hari_b and start_a < end_b and start_b < end_a
    return jadwal_a.strip().lower() == jadwal_b.strip().lower()


def hitung_nilai_dan_huruf(tugas: float, uts: float, uas: float):
    """Menghitung Nilai Akhir = 30% Tugas + 30% UTS + 40% UAS beserta huruf mutu & bobot."""
    akhir = round((0.30 * tugas) + (0.30 * uts) + (0.40 * uas), 1)
    if akhir >= 85.0:
        return akhir, "A", 4.0
    if akhir >= 70.0:
        return akhir, "B", 3.0
    if akhir >= 55.0:
        return akhir, "C", 2.0
    if akhir >= 40.0:
        return akhir, "D", 1.0
    return akhir, "E", 0.0


def init_db():
    """Membuat 5 tabel relasional (users, matakuliah, krs, attendance_logs, grades) dan mengisi seed data Figma."""
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Tabel users (Mendukung relasi Dosen PA & riwayat semester untuk IPK - Revisi T6)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'dosen', 'mahasiswa')),
            nim_nip TEXT,
            dosen_pa_id INTEGER,
            sks_lalu INTEGER DEFAULT 0,
            ipk_lalu REAL DEFAULT 0.0,
            FOREIGN KEY (dosen_pa_id) REFERENCES users(id)
        )
        """
    )

    # 2. Tabel matakuliah (Menyimpan master MK, jadwal, kuota, dan status sesi presensi real-time)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS matakuliah (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kode_mk TEXT UNIQUE NOT NULL,
            nama_mk TEXT NOT NULL,
            sks INTEGER NOT NULL,
            jadwal TEXT NOT NULL,
            kuota INTEGER DEFAULT 40,
            total_pertemuan INTEGER DEFAULT 4,
            sesi_dibuka INTEGER DEFAULT 0,
            token_sesi TEXT DEFAULT 'HADIR1',
            dosen_id INTEGER,
            FOREIGN KEY (dosen_id) REFERENCES users(id)
        )
        """
    )

    # 3. Tabel krs (Pengajuan KRS mahasiswa, status persetujuan Dosen PA, dan jumlah hadir)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS krs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mahasiswa_id INTEGER NOT NULL,
            mk_id INTEGER NOT NULL,
            semester_aktif TEXT DEFAULT 'Ganjil 2026/2027',
            status_persetujuan TEXT DEFAULT 'Menunggu Dosen'
                CHECK(status_persetujuan IN ('Menunggu Dosen', 'Disetujui', 'Ditolak')),
            jumlah_hadir INTEGER DEFAULT 0,
            created_at TEXT,
            UNIQUE(mahasiswa_id, mk_id),
            FOREIGN KEY (mahasiswa_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (mk_id) REFERENCES matakuliah(id) ON DELETE CASCADE
        )
        """
    )

    # 4. Tabel attendance_logs (Log riwayat check-in presensi real-time mahasiswa & pencegahan duplikasi)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mk_id INTEGER NOT NULL,
            mahasiswa_id INTEGER NOT NULL,
            pertemuan_ke INTEGER NOT NULL,
            token_sesi TEXT,
            tanggal TEXT,
            status_hadir TEXT DEFAULT 'Hadir',
            waktu_checkin TEXT,
            UNIQUE(mk_id, mahasiswa_id, token_sesi, tanggal),
            FOREIGN KEY (mk_id) REFERENCES matakuliah(id) ON DELETE CASCADE,
            FOREIGN KEY (mahasiswa_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    # 5. Tabel grades (Komponen nilai Tugas 30%, UTS 30%, UAS 40%, Nilai Akhir & Grade)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            krs_id INTEGER UNIQUE NOT NULL,
            nilai_tugas REAL DEFAULT 0.0,
            nilai_uts REAL DEFAULT 0.0,
            nilai_uas REAL DEFAULT 0.0,
            nilai_akhir REAL DEFAULT 0.0,
            nilai_huruf TEXT DEFAULT '-',
            bobot_mutu REAL DEFAULT 0.0,
            FOREIGN KEY (krs_id) REFERENCES krs(id) ON DELETE CASCADE
        )
        """
    )

    # Cek apakah seed data sudah ada
    user_count = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if user_count == 0:
        cur.execute(
            """
            INSERT INTO users (username, password_hash, full_name, role, nim_nip, dosen_pa_id, sks_lalu, ipk_lalu)
            VALUES (?, ?, ?, 'admin', '198801012015041001', NULL, 0, 0.0)
            """,
            ("admin", generate_password_hash("admin123"), "Budi Santoso, S.Kom"),
        )
        cur.execute(
            """
            INSERT INTO users (username, password_hash, full_name, role, nim_nip, dosen_pa_id, sks_lalu, ipk_lalu)
            VALUES (?, ?, ?, 'dosen', '198205122009121003', NULL, 0, 0.0)
            """,
            ("dosen", generate_password_hash("dosen123"), "Dr. Hendra Wijaya, M.T."),
        )
        dosen_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO users (username, password_hash, full_name, role, nim_nip, dosen_pa_id, sks_lalu, ipk_lalu)
            VALUES (?, ?, ?, 'mahasiswa', '5233151001', ?, 40, 3.65)
            """,
            ("mhs1", generate_password_hash("mhs123"), "Andi Pratama", dosen_id),
        )
        mhs1_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO users (username, password_hash, full_name, role, nim_nip, dosen_pa_id, sks_lalu, ipk_lalu)
            VALUES (?, ?, ?, 'mahasiswa', '5233151002', ?, 40, 3.45)
            """,
            ("mhs2", generate_password_hash("mhs123"), "Siti Rahmawati", dosen_id),
        )
        mhs2_id = cur.lastrowid

        courses_seed = [
            ("TI-301", "Manajemen Proyek TI", 3, "Senin, 08:00 - 10:30", 40, 4, 1, "MPTI04", dosen_id),
            ("TI-302", "Rekayasa Perangkat Lunak", 3, "Rabu, 08:00 - 10:30", 40, 4, 0, "RPL004", dosen_id),
            ("TI-303", "Kecerdasan Buatan", 3, "Kamis, 10:00 - 12:30", 40, 4, 0, "AI2026", dosen_id),
            ("TI-304", "Keamanan Jaringan", 3, "Jumat, 08:00 - 10:30", 40, 4, 0, "NETSEC", dosen_id),
        ]
        mk_ids = {}
        for kode, nama, sks, jadwal, kuota, tot_p, dibuka, token, d_id in courses_seed:
            cur.execute(
                """
                INSERT INTO matakuliah (kode_mk, nama_mk, sks, jadwal, kuota, total_pertemuan, sesi_dibuka, token_sesi, dosen_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (kode, nama, sks, jadwal, kuota, tot_p, dibuka, token, d_id),
            )
            mk_ids[kode] = cur.lastrowid

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        cur.execute(
            """
            INSERT INTO krs (mahasiswa_id, mk_id, status_persetujuan, jumlah_hadir, created_at)
            VALUES (?, ?, 'Disetujui', 3, ?)
            """,
            (mhs1_id, mk_ids["TI-301"], now_str),
        )
        krs1_id = cur.lastrowid
        akhir1, huruf1, bobot1 = hitung_nilai_dan_huruf(85.0, 85.0, 86.25)
        cur.execute(
            """
            INSERT INTO grades (krs_id, nilai_tugas, nilai_uts, nilai_uas, nilai_akhir, nilai_huruf, bobot_mutu)
            VALUES (?, 85.0, 85.0, 86.25, ?, ?, ?)
            """,
            (krs1_id, akhir1, huruf1, bobot1),
        )

        cur.execute(
            """
            INSERT INTO krs (mahasiswa_id, mk_id, status_persetujuan, jumlah_hadir, created_at)
            VALUES (?, ?, 'Menunggu Dosen', 0, ?)
            """,
            (mhs1_id, mk_ids["TI-302"], now_str),
        )
        krs2_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO grades (krs_id, nilai_tugas, nilai_uts, nilai_uas, nilai_akhir, nilai_huruf, bobot_mutu)
            VALUES (?, 0.0, 0.0, 0.0, 0.0, '-', 0.0)
            """,
            (krs2_id,),
        )

        cur.execute(
            """
            INSERT INTO krs (mahasiswa_id, mk_id, status_persetujuan, jumlah_hadir, created_at)
            VALUES (?, ?, 'Disetujui', 4, ?)
            """,
            (mhs2_id, mk_ids["TI-301"], now_str),
        )
        krs3_id = cur.lastrowid
        akhir3, huruf3, bobot3 = hitung_nilai_dan_huruf(78.0, 75.0, 80.0)
        cur.execute(
            """
            INSERT INTO grades (krs_id, nilai_tugas, nilai_uts, nilai_uas, nilai_akhir, nilai_huruf, bobot_mutu)
            VALUES (?, 78.0, 75.0, 80.0, ?, ?, ?)
            """,
            (krs3_id, akhir3, huruf3, bobot3),
        )

        conn.commit()
    conn.close()


def verify_user_credentials(username: str, password: str):
    """Memverifikasi login menggunakan parameterized query dan check_password_hash (NFR-01)."""
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if user and check_password_hash(user["password_hash"], password):
        return dict(user)
    return None
