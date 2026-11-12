import sqlite3

DB_NAME = "akademik.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def hitung_huruf_mutu(nilai_akhir):
    if nilai_akhir >= 85:
        return "A"
    elif nilai_akhir >= 75:
        return "B"
    elif nilai_akhir >= 60:
        return "C"
    elif nilai_akhir >= 50:
        return "D"
    else:
        return "E"

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    # 1. Tabel Users (Admin, Dosen, Mahasiswa)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        nama TEXT NOT NULL,
        nomor_induk TEXT NOT NULL,
        role TEXT NOT NULL
    )''')

    # 2. Tabel Mata Kuliah (Data Master)
    c.execute('''CREATE TABLE IF NOT EXISTS matakuliah (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kode_mk TEXT UNIQUE NOT NULL,
        nama_mk TEXT NOT NULL,
        sks INTEGER NOT NULL,
        jadwal TEXT NOT NULL,
        dosen_id INTEGER,
        sesi_presensi_aktif INTEGER DEFAULT 0,
        total_pertemuan INTEGER DEFAULT 1
    )''')

    # 3. Tabel KRS, Presensi & Evaluasi Nilai
    c.execute('''CREATE TABLE IF NOT EXISTS krs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mahasiswa_id INTEGER NOT NULL,
        mk_id INTEGER NOT NULL,
        status_krs TEXT DEFAULT 'Pending',
        hadir_count INTEGER DEFAULT 0,
        nilai_tugas REAL DEFAULT 0,
        nilai_uts REAL DEFAULT 0,
        nilai_uas REAL DEFAULT 0,
        nilai_akhir REAL DEFAULT 0,
        nilai_huruf TEXT DEFAULT '-',
        UNIQUE(mahasiswa_id, mk_id)
    )''')

    # Seed Data Awal jika tabel masih kosong
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        users_seed = [
            ("admin", "admin123", "Budi Santoso, S.Kom (Admin)", "ADM-001", "admin"),
            ("dosen", "dosen123", "Dr. Hendra Wijaya, M.T.", "DSN-101", "dosen"),
            ("mhs1", "mhs123", "Andi Pratama", "2301001", "mahasiswa"),
            ("mhs2", "mhs123", "Siti Rahmawati", "2301002", "mahasiswa")
        ]
        c.executemany(
            "INSERT INTO users (username, password, nama, nomor_induk, role) VALUES (?, ?, ?, ?, ?)",
            users_seed
        )

        c.execute("SELECT id FROM users WHERE username='dosen'")
        dosen_id = c.fetchone()[0]

        mk_seed = [
            ("TI-301", "Manajemen Proyek TI", 3, "Senin, 08:00 - 10:30", dosen_id, 1, 4),
            ("TI-302", "Rekayasa Perangkat Lunak", 3, "Rabu, 10:30 - 13:00", dosen_id, 0, 4),
            ("TI-303", "Kecerdasan Buatan", 3, "Kamis, 13:30 - 16:00", dosen_id, 0, 4),
            ("TI-304", "Keamanan Jaringan", 2, "Jumat, 08:00 - 09:40", dosen_id, 0, 4)
        ]
        c.executemany(
            "INSERT INTO matakuliah (kode_mk, nama_mk, sks, jadwal, dosen_id, sesi_presensi_aktif, total_pertemuan) VALUES (?, ?, ?, ?, ?, ?, ?)",
            mk_seed
        )

        c.execute("SELECT id FROM users WHERE username='mhs1'")
        mhs1_id = c.fetchone()[0]
        c.execute(
            "INSERT INTO krs (mahasiswa_id, mk_id, status_krs, hadir_count, nilai_tugas, nilai_uts, nilai_uas, nilai_akhir, nilai_huruf) VALUES (?, 1, 'Disetujui', 3, 85, 80, 90, 85.5, 'A')",
            (mhs1_id,)
        )
        c.execute(
            "INSERT INTO krs (mahasiswa_id, mk_id, status_krs, hadir_count) VALUES (?, 2, 'Pending', 0)",
            (mhs1_id,)
        )

    conn.commit()
    conn.close()
