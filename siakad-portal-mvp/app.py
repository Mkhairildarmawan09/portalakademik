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

