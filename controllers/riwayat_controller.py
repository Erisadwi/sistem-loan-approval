from flask import Blueprint, render_template, session, redirect, request
from utils.db import get_db_connection
import math

riwayat_bp = Blueprint('riwayat', __name__)

@riwayat_bp.route('/riwayat')
def riwayat():

    # cek login
    if 'user' not in session:
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # =========================
    # PAGINATION
    # =========================
    per_page = 10

    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * per_page

    # =========================
    # SEARCH
    # =========================
    search = request.args.get('search', '')

    # =========================
    # COUNT QUERY
    # =========================
    count_query = """
        SELECT COUNT(*) as total
        FROM log_activity l
        JOIN users u ON l.id_user = u.id_user
        WHERE 1=1
    """

    count_params = []

    if search:
        count_query += """
            AND (
                CAST(l.id_log AS CHAR) LIKE %s
                OR CAST(l.id_pengajuan AS CHAR) LIKE %s
                OR u.nama LIKE %s
                OR l.jenis_aktivitas LIKE %s
                OR l.aktivitas LIKE %s
                OR CAST(l.waktu AS CHAR) LIKE %s
            )
        """

        keyword = f"%{search}%"

        count_params.extend([
            keyword,
            keyword,
            keyword,
            keyword,
            keyword,
            keyword
        ])

    cursor.execute(count_query, count_params)

    total_data = cursor.fetchone()['total']

    total_pages = math.ceil(total_data / per_page)

    # =========================
    # DATA QUERY
    # =========================
    data_query = """
        SELECT
            l.id_log,
            l.id_pengajuan,
            u.nama,
            l.jenis_aktivitas,
            l.aktivitas,
            l.waktu
        FROM log_activity l
        JOIN users u ON l.id_user = u.id_user
        WHERE 1=1
    """

    data_params = []

    if search:
        data_query += """
            AND (
                CAST(l.id_log AS CHAR) LIKE %s
                OR CAST(l.id_pengajuan AS CHAR) LIKE %s
                OR u.nama LIKE %s
                OR l.jenis_aktivitas LIKE %s
                OR l.aktivitas LIKE %s
                OR CAST(l.waktu AS CHAR) LIKE %s
            )
        """

        keyword = f"%{search}%"

        data_params.extend([
            keyword,
            keyword,
            keyword,
            keyword,
            keyword,
            keyword
        ])

    data_query += """
        ORDER BY l.waktu DESC
        LIMIT %s OFFSET %s
    """

    data_params.extend([per_page, offset])

    cursor.execute(data_query, data_params)

    logs = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'riwayat.html',
        logs=logs,
        search=search,
        page=page,
        total_pages=total_pages
    )