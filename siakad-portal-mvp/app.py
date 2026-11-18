"""
Controller Utama Aplikasi Web SIAKAD Portal MVP (Flask 3.0.3)
Disesuaikan 100% dengan Desain UI/UX Figma & Revisi Audit MPTI (T1 s.d. T13)
"""

import os
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection, init_db, verify_user_credentials, hitung_nilai_dan_huruf

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "siakad-portal-mvp-secret-2026")

# Pengaturan DEMO_MODE untuk menampilkan/menyembunyikan kotak akun demo di halaman login (Revisi T13)
DEMO_MODE = os.getenv("DEMO_MODE", "True").lower() == "true"
MAX_SKS_KRS = 24


def login_required(allowed_roles=None):
    """Decorator proteksi sesi dan otorisasi berbasis peran (FR-02 & NFR-01)."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                flash("Silakan login terlebih dahulu untuk mengakses halaman tersebut.", "warning")
                return redirect(url_for("login"))
            if allowed_roles and session.get("role") not in allowed_roles:
                flash("Akses ditolak: Anda tidak memiliki izin untuk halaman/aksi tersebut!", "danger")
                return redirect(url_for("index"))
            return fn(*args, **kwargs)
        return wrapper
    return decorator


@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    role = session.get("role")
    if role == "admin":
        return redirect(url_for("dashboard_admin"))
    if role == "dosen":
        return redirect(url_for("dashboard_dosen"))
    return redirect(url_for("dashboard_mahasiswa"))


# ==============================================================================
# SPRINT 1: AUTENTIKASI MULTI-ROLE, UBAH KATA SANDI (FR-17) & MASTER MATA KULIAH
# ==============================================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = verify_user_credentials(username, password)
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["full_name"] = user["full_name"]
            session["role"] = user["role"]
            session["nim_nip"] = user["nim_nip"]
            flash(f"Selamat datang, {user['full_name']}!", "success")
            return redirect(url_for("index"))
        flash("Username atau password salah!", "danger")
    return render_template("login.html", demo_mode=DEMO_MODE)


@app.route("/logout")
def logout():
    session.clear()
    flash("Anda telah berhasil keluar dari sistem.", "info")
    return redirect(url_for("login"))


@app.route("/ubah_password", methods=["POST"])
@login_required(["admin", "dosen", "mahasiswa"])
def ubah_password():
    """Fitur ubah kata sandi mandiri pengguna (US-03 / FR-17)."""
    pass_lama = request.form.get("password_lama", "")
    pass_baru = request.form.get("password_baru", "").strip()
    if len(pass_baru) < 6:
        flash("Kata sandi baru minimal harus 6 karakter.", "warning")
        return redirect(url_for("index"))

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    if not user or not check_password_hash(user["password_hash"], pass_lama):
        conn.close()
        flash("Kata sandi lama tidak sesuai!", "danger")
        return redirect(url_for("index"))

    conn.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (generate_password_hash(pass_baru), session["user_id"]),
    )
    conn.commit()
    conn.close()
    flash("Kata sandi akun berhasil diperbarui!", "success")
    return redirect(url_for("index"))


@app.route("/admin")
@login_required(["admin"])
def dashboard_admin():
    conn = get_db_connection()
    daftar_mk = conn.execute("SELECT * FROM matakuliah ORDER BY kode_mk ASC").fetchall()
    conn.close()
    return render_template("dashboard_admin.html", daftar_mk=daftar_mk)


@app.route("/tambah_mk", methods=["POST"])
@login_required(["admin"])
def tambah_mk():
    kode_mk = request.form.get("kode_mk", "").strip().upper()
    nama_mk = request.form.get("nama_mk", "").strip()
    sks_raw = request.form.get("sks", "3").strip()
    jadwal = request.form.get("jadwal", "").strip()

    if not kode_mk or not nama_mk or not jadwal:
        flash("Seluruh kolom mata kuliah (Kode, Nama, SKS, dan Jadwal) wajib diisi!", "warning")
        return redirect(url_for("dashboard_admin"))

    try:
        sks = int(sks_raw)
        if sks < 1 or sks > 6:
            raise ValueError
    except ValueError:
        flash("Beban SKS harus berupa angka antara 1 hingga 6.", "warning")
        return redirect(url_for("dashboard_admin"))

    conn = get_db_connection()
    existing = conn.execute("SELECT id FROM matakuliah WHERE kode_mk = ?", (kode_mk,)).fetchone()
    if existing:
        conn.close()
        flash("Kode Mata Kuliah sudah terdaftar!", "danger")
        return redirect(url_for("dashboard_admin"))

    dosen = conn.execute("SELECT id FROM users WHERE role = 'dosen' LIMIT 1").fetchone()
    dosen_id = dosen["id"] if dosen else None
    conn.execute(
        """
        INSERT INTO matakuliah (kode_mk, nama_mk, sks, jadwal, dosen_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (kode_mk, nama_mk, sks, jadwal, dosen_id),
    )
    conn.commit()
    conn.close()
    flash(f"Mata kuliah {kode_mk} - {nama_mk} berhasil ditambahkan!", "success")
    return redirect(url_for("dashboard_admin"))


@app.route("/edit_mk/<int:mk_id>", methods=["POST"])
@login_required(["admin"])
def edit_mk(mk_id):
    """Fitur Ubah/Edit Mata Kuliah untuk melengkapi CRUD penuh pada US-04 / FR-03 (Revisi T7)."""
    kode_mk = request.form.get("kode_mk", "").strip().upper()
    nama_mk = request.form.get("nama_mk", "").strip()
    sks_raw = request.form.get("sks", "3").strip()
    jadwal = request.form.get("jadwal", "").strip()

    if not kode_mk or not nama_mk or not jadwal:
        flash("Kode MK, Nama MK, SKS, dan Jadwal tidak boleh kosong!", "warning")
        return redirect(url_for("dashboard_admin"))

    try:
        sks = int(sks_raw)
    except ValueError:
        flash("Beban SKS harus berupa angka valid!", "warning")
        return redirect(url_for("dashboard_admin"))

    conn = get_db_connection()
    duplikat = conn.execute(
        "SELECT id FROM matakuliah WHERE kode_mk = ? AND id != ?", (kode_mk, mk_id)
    ).fetchone()
    if duplikat:
        conn.close()
        flash("Kode Mata Kuliah sudah digunakan oleh mata kuliah lain!", "danger")
        return redirect(url_for("dashboard_admin"))

    conn.execute(
        """
        UPDATE matakuliah
        SET kode_mk = ?, nama_mk = ?, sks = ?, jadwal = ?
        WHERE id = ?
        """,
        (kode_mk, nama_mk, sks, jadwal, mk_id),
    )
    conn.commit()
    conn.close()
    flash(f"Data mata kuliah {kode_mk} berhasil diperbarui!", "success")
    return redirect(url_for("dashboard_admin"))


@app.route("/hapus_mk/<int:mk_id>", methods=["POST", "GET"])
@login_required(["admin"])
def hapus_mk(mk_id):
    conn = get_db_connection()
    mk = conn.execute("SELECT kode_mk, nama_mk FROM matakuliah WHERE id = ?", (mk_id,)).fetchone()
    if mk:
        conn.execute("DELETE FROM matakuliah WHERE id = ?", (mk_id,))
        conn.commit()
        flash(f"Mata kuliah {mk['kode_mk']} ({mk['nama_mk']}) berhasil dihapus!", "info")
    conn.close()
    return redirect(url_for("dashboard_admin"))


# ==============================================================================
# SPRINT 2 & 3: PENGELOLAAN KRS, PRESENSI REAL-TIME & EVALUASI NILAI (KHS)
# ==============================================================================
@app.route("/mahasiswa")
@login_required(["mahasiswa"])
def dashboard_mahasiswa():
    mhs_id = session["user_id"]
    conn = get_db_connection()
    user_info = conn.execute("SELECT * FROM users WHERE id = ?", (mhs_id,)).fetchone()
    semua_mk = conn.execute("SELECT * FROM matakuliah ORDER BY kode_mk ASC").fetchall()

    krs_rows = conn.execute(
        """
        SELECT k.id AS krs_id, k.mk_id, k.status_persetujuan, k.jumlah_hadir,
               m.kode_mk, m.nama_mk, m.sks, m.jadwal, m.total_pertemuan, m.sesi_dibuka,
               COALESCE(g.nilai_tugas, 0) AS nilai_tugas,
               COALESCE(g.nilai_uts, 0) AS nilai_uts,
               COALESCE(g.nilai_uas, 0) AS nilai_uas,
               COALESCE(g.nilai_akhir, 0) AS nilai_akhir,
               COALESCE(g.nilai_huruf, '-') AS nilai_huruf,
               COALESCE(g.bobot_mutu, 0) AS bobot_mutu
        FROM krs k
        JOIN matakuliah m ON m.id = k.mk_id
        LEFT JOIN grades g ON g.krs_id = k.id
        WHERE k.mahasiswa_id = ?
        ORDER BY m.kode_mk ASC
        """,
        (mhs_id,),
    ).fetchall()
    conn.close()

    mk_diambil_ids = {r["mk_id"] for r in krs_rows}
    total_sks_diajukan = sum(r["sks"] for r in krs_rows if r["status_persetujuan"] != "Ditolak")

    # Perhitungan IPS Semester Aktif & IPK Kumulatif (FR-15 / US-19)
    sks_dinilai = sum(r["sks"] for r in krs_rows if r["nilai_huruf"] != "-")
    mutu_semester = sum(r["sks"] * r["bobot_mutu"] for r in krs_rows if r["nilai_huruf"] != "-")
    ips = round(mutu_semester / sks_dinilai, 2) if sks_dinilai > 0 else 0.00

    sks_lalu = user_info["sks_lalu"] if user_info else 0
    ipk_lalu = user_info["ipk_lalu"] if user_info else 0.0
    total_sks_kumulatif = sks_lalu + sks_dinilai
    if total_sks_kumulatif > 0:
        ipk = round(((sks_lalu * ipk_lalu) + mutu_semester) / total_sks_kumulatif, 2)
    else:
        ipk = 0.00

    return render_template(
        "dashboard_mahasiswa.html",
        semua_mk=semua_mk,
        krs_list=krs_rows,
        mk_diambil_ids=mk_diambil_ids,
        total_sks=total_sks_diajukan,
        max_sks=MAX_SKS_KRS,
        ips=ips,
        ipk=ipk,
    )


@app.route("/ajukan_krs/<int:mk_id>", methods=["POST"])
@login_required(["mahasiswa"])
def ajukan_krs(mk_id):
    """Pengajuan KRS Mahasiswa dengan validasi batas 24 SKS (FR-08) & deteksi jadwal bentrok (FR-09)."""
    mhs_id = session["user_id"]
    conn = get_db_connection()

    mk_target = conn.execute("SELECT * FROM matakuliah WHERE id = ?", (mk_id,)).fetchone()
    if not mk_target:
        conn.close()
        flash("Mata kuliah tidak ditemukan!", "danger")
        return redirect(url_for("dashboard_mahasiswa"))

    krs_aktif = conn.execute(
        """
        SELECT k.mk_id, m.kode_mk, m.nama_mk, m.sks, m.jadwal
        FROM krs k
        JOIN matakuliah m ON m.id = k.mk_id
        WHERE k.mahasiswa_id = ? AND k.status_persetujuan != 'Ditolak'
        """,
        (mhs_id,),
    ).fetchall()

    # 1. Cek duplikasi pengajuan
    if any(r["mk_id"] == mk_id for r in krs_aktif):
        conn.close()
        flash(f"Mata kuliah {mk_target['kode_mk']} sudah ada di dalam daftar KRS Anda.", "warning")
        return redirect(url_for("dashboard_mahasiswa"))

    # 2. Validasi batas maksimum 24 SKS (US-09 / FR-08)
    total_sks_sekarang = sum(r["sks"] for r in krs_aktif)
    if total_sks_sekarang + mk_target["sks"] > MAX_SKS_KRS:
        conn.close()
        flash(
            f"Pengajuan ditolak: Penambahan {mk_target['kode_mk']} ({mk_target['sks']} SKS) "
            f"melebihi batas maksimal {MAX_SKS_KRS} SKS!",
            "danger",
        )
        return redirect(url_for("dashboard_mahasiswa"))

    # 3. Validasi deteksi bentrok jadwal (US-10 / FR-09)
    for r in krs_aktif:
        if r["jadwal"].strip().lower() == mk_target["jadwal"].strip().lower():
            conn.close()
            flash(
                f"Jadwal bentrok! {mk_target['kode_mk']} memiliki jadwal yang sama "
                f"({mk_target['jadwal']}) dengan {r['kode_mk']} ({r['nama_mk']}).",
                "danger",
            )
            return redirect(url_for("dashboard_mahasiswa"))

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO krs (mahasiswa_id, mk_id, status_persetujuan, jumlah_hadir, created_at)
        VALUES (?, ?, 'Menunggu Dosen', 0, ?)
        """,
        (mhs_id, mk_id, now_str),
    )
    krs_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO grades (krs_id, nilai_tugas, nilai_uts, nilai_uas, nilai_akhir, nilai_huruf, bobot_mutu)
        VALUES (?, 0.0, 0.0, 0.0, 0.0, '-', 0.0)
        """,
        (krs_id,),
    )
    conn.commit()
    conn.close()
    flash(f"Berhasil mengajukan {mk_target['kode_mk']} - {mk_target['nama_mk']} ke KRS!", "success")
    return redirect(url_for("dashboard_mahasiswa"))


@app.route("/hadir/<int:krs_id>", methods=["POST"])
@login_required(["mahasiswa"])
def klik_hadir(krs_id):
    """Pencatatan kehadiran real-time oleh mahasiswa saat sesi dibuka Dosen (US-14 / FR-12)."""
    mhs_id = session["user_id"]
    conn = get_db_connection()
    row = conn.execute(
        """
        SELECT k.id, k.mahasiswa_id, k.mk_id, k.status_persetujuan, k.jumlah_hadir,
               m.kode_mk, m.nama_mk, m.total_pertemuan, m.sesi_dibuka, m.token_sesi
        FROM krs k
        JOIN matakuliah m ON m.id = k.mk_id
        WHERE k.id = ? AND k.mahasiswa_id = ?
        """,
        (krs_id, mhs_id),
    ).fetchone()

    if not row:
        conn.close()
        flash("Data KRS tidak ditemukan!", "danger")
        return redirect(url_for("dashboard_mahasiswa"))

    if row["status_persetujuan"] != "Disetujui":
        conn.close()
        flash("Presensi hanya dapat dilakukan pada mata kuliah yang KRS-nya sudah Disetujui Dosen!", "warning")
        return redirect(url_for("dashboard_mahasiswa"))

    if not row["sesi_dibuka"]:
        conn.close()
        flash(f"Sesi presensi untuk {row['kode_mk']} sedang ditutup!", "warning")
        return redirect(url_for("dashboard_mahasiswa"))

    hadir_baru = min(row["jumlah_hadir"] + 1, row["total_pertemuan"])
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("UPDATE krs SET jumlah_hadir = ? WHERE id = ?", (hadir_baru, krs_id))
    conn.execute(
        """
        INSERT INTO attendance_logs (mk_id, mahasiswa_id, pertemuan_ke, token_sesi, tanggal, status_hadir, waktu_checkin)
        VALUES (?, ?, ?, ?, ?, 'Hadir', ?)
        """,
        (row["mk_id"], mhs_id, hadir_baru, row["token_sesi"], now_str[:10], now_str),
    )
    conn.commit()
    conn.close()
    flash(f"Presensi real-time berhasil dicatat untuk {row['kode_mk']} ({hadir_baru}/{row['total_pertemuan']})!", "success")
    return redirect(url_for("dashboard_mahasiswa"))


@app.route("/dosen")
@login_required(["dosen"])
def dashboard_dosen():
    conn = get_db_connection()
    daftar_mk = conn.execute("SELECT * FROM matakuliah ORDER BY kode_mk ASC").fetchall()
    daftar_krs = conn.execute(
        """
        SELECT k.id AS krs_id, k.status_persetujuan, k.jumlah_hadir,
               u.full_name AS nama_mhs, u.nim_nip,
               m.kode_mk, m.nama_mk, m.total_pertemuan,
               COALESCE(g.nilai_tugas, 0) AS nilai_tugas,
               COALESCE(g.nilai_uts, 0) AS nilai_uts,
               COALESCE(g.nilai_uas, 0) AS nilai_uas,
               COALESCE(g.nilai_akhir, 0) AS nilai_akhir,
               COALESCE(g.nilai_huruf, '-') AS nilai_huruf
        FROM krs k
        JOIN users u ON u.id = k.mahasiswa_id
        JOIN matakuliah m ON m.id = k.mk_id
        LEFT JOIN grades g ON g.krs_id = k.id
        ORDER BY m.kode_mk ASC, u.full_name ASC
        """
    ).fetchall()
    conn.close()
    return render_template("dashboard_dosen.html", daftar_mk=daftar_mk, daftar_krs=daftar_krs)


@app.route("/toggle_presensi/<int:mk_id>", methods=["POST"])
@login_required(["dosen"])
def toggle_presensi(mk_id):
    """Membuka atau menutup sesi presensi real-time kelas oleh Dosen (US-13 / FR-11)."""
    conn = get_db_connection()
    mk = conn.execute("SELECT * FROM matakuliah WHERE id = ?", (mk_id,)).fetchone()
    if mk:
        status_baru = 0 if mk["sesi_dibuka"] else 1
        conn.execute("UPDATE matakuliah SET sesi_dibuka = ? WHERE id = ?", (status_baru, mk_id))
        conn.commit()
        label = "DIBUKA (REAL-TIME)" if status_baru else "DITUTUP"
        flash(f"Status sesi presensi {mk['kode_mk']} berhasil diubah menjadi {label}.", "success" if status_baru else "warning")
    conn.close()
    return redirect(url_for("dashboard_dosen"))


@app.route("/validasi_krs/<int:krs_id>/<string:aksi>", methods=["POST"])
@login_required(["dosen"])
def validasi_krs(krs_id, aksi):
    """Menyetujui atau menolak pengajuan KRS mahasiswa oleh Dosen PA (US-11 / FR-10)."""
    status_map = {"setujui": "Disetujui", "tolak": "Ditolak"}
    if aksi not in status_map:
        flash("Aksi validasi tidak dikenali!", "danger")
        return redirect(url_for("dashboard_dosen"))

    status_baru = status_map[aksi]
    conn = get_db_connection()
    conn.execute("UPDATE krs SET status_persetujuan = ? WHERE id = ?", (status_baru, krs_id))
    conn.commit()
    conn.close()
    flash(f"Status KRS mahasiswa berhasil diperbarui menjadi '{status_baru}'.", "success" if aksi == "setujui" else "warning")
    return redirect(url_for("dashboard_dosen"))


@app.route("/input_nilai/<int:krs_id>", methods=["POST"])
@login_required(["dosen"])
def input_nilai(krs_id):
    """Input nilai Tugas (30%), UTS (30%), UAS (40%) & kalkulasi otomatis huruf mutu (US-17, US-18 / FR-14)."""
    try:
        tugas = float(request.form.get("nilai_tugas", 0))
        uts = float(request.form.get("nilai_uts", 0))
        uas = float(request.form.get("nilai_uas", 0))
        if not (0 <= tugas <= 100 and 0 <= uts <= 100 and 0 <= uas <= 100):
            raise ValueError
    except ValueError:
        flash("Nilai Tugas, UTS, dan UAS harus berupa angka antara 0 sampai 100!", "danger")
        return redirect(url_for("dashboard_dosen"))

    akhir, huruf, bobot = hitung_nilai_dan_huruf(tugas, uts, uas)
    conn = get_db_connection()
    existing = conn.execute("SELECT id FROM grades WHERE krs_id = ?", (krs_id,)).fetchone()
    if existing:
        conn.execute(
            """
            UPDATE grades
            SET nilai_tugas = ?, nilai_uts = ?, nilai_uas = ?, nilai_akhir = ?, nilai_huruf = ?, bobot_mutu = ?
            WHERE krs_id = ?
            """,
            (tugas, uts, uas, akhir, huruf, bobot, krs_id),
        )
    else:
        conn.execute(
            """
            INSERT INTO grades (krs_id, nilai_tugas, nilai_uts, nilai_uas, nilai_akhir, nilai_huruf, bobot_mutu)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (krs_id, tugas, uts, uas, akhir, huruf, bobot),
        )
    conn.commit()
    conn.close()
    flash(f"Nilai berhasil disimpan! Nilai Akhir: {akhir} (Grade {huruf}).", "success")
    return redirect(url_for("dashboard_dosen"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)
