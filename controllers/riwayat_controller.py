from flask import Blueprint, render_template, session, redirect
from utils.db import get_db_connection

riwayat_bp = Blueprint('riwayat', __name__)

@riwayat_bp.route('/riwayat')
def riwayat():

    # cek login
    if 'user' not in session:
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ambil data log activity
    cursor.execute("""
        SELECT *
        FROM log_activity
        ORDER BY waktu DESC
    """)

    logs = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'riwayat.html',
        logs=logs
    )