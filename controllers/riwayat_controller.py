from flask import Blueprint, render_template, session, redirect, request
from utils.db import get_db_connection

riwayat_bp = Blueprint('riwayat', __name__)

@riwayat_bp.route('/riwayat')
def riwayat():

    # cek login
    if 'user' not in session:
        return redirect('/')

    # ambil keyword pencarian
    search = request.args.get('search', '')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT 
            l.id_log,
            l.id_pengajuan,
            l.id_user,
            u.nama,
            l.jenis_aktivitas,
            l.aktivitas,
            l.waktu
        FROM log_activity l
        JOIN users u ON l.id_user = u.id_user
    """

    params = []

    # jika ada pencarian
    if search:
        query += """
            WHERE 
                l.id_pengajuan LIKE %s
                OR u.nama LIKE %s
                OR l.jenis_aktivitas LIKE %s
                OR l.aktivitas LIKE %s
        """

        keyword = f"%{search}%"

        params.extend([
            keyword,
            keyword,
            keyword,
            keyword
        ])

    query += " ORDER BY l.waktu DESC"

    cursor.execute(query, params)

    logs = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'riwayat.html',
        logs=logs,
        search=search
    )