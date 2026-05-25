from flask import Blueprint, render_template, request, redirect, session
from utils.db import get_db_connection
from datetime import datetime
import bcrypt


auth = Blueprint('auth', __name__)


@auth.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
       
        email = request.form['email'].strip()
        password = request.form['password'].strip()


        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)


        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()


        cursor.close()
        conn.close()


        if user:
            stored_password = user['password']


            if isinstance(stored_password, str):
                stored_password = stored_password.encode('utf-8')


            if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                session['user'] = user['id_user']
                session['nama'] = user['nama']
                return redirect('/dashboard')
            else:
                return "Password salah"
        else:
            return "User tidak ditemukan"


    return render_template('login.html')




@auth.route('/dashboard')
def dashboard():

    if 'user' not in session:
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM basis_kasus")
    total = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) AS approved
        FROM basis_kasus
        WHERE loan_status = 'Approved'
    """)
    approved = cursor.fetchone()['approved']

    cursor.execute("""
        SELECT COUNT(*) AS rejected
        FROM basis_kasus
        WHERE loan_status = 'Rejected'
    """)
    rejected = cursor.fetchone()['rejected']

    pending = 0

    cursor.execute("""
        SELECT 
            MONTH(tanggal_masuk) AS bulan,
            COUNT(*) AS jumlah
        FROM basis_kasus
        GROUP BY MONTH(tanggal_masuk)
        ORDER BY MONTH(tanggal_masuk)
    """)

    hasil = cursor.fetchall()

    bulan_map = {
        1: "Januari",
        2: "Februari",
        3: "Maret",
        4: "April",
        5: "Mei",
        6: "Juni",
        7: "Juli",
        8: "Agustus",
        9: "September",
        10: "Oktober",
        11: "November",
        12: "Desember"
    }

    labels = []
    values = []

    for row in hasil:
        labels.append(bulan_map[row['bulan']])
        values.append(row['jumlah'])

    total_chart = sum(values)

    if total_chart == 0:
        percentages = [0, 0, 0, 0]
    else:
        percentages = [
            (v / total_chart) * 360
            for v in values
        ]
    
    cursor.close()
    conn.close()

    return render_template(
        'dashboard.html',
        nama=session['nama'],
        total=total,
        approved=approved,
        rejected=rejected,
        pending=pending,
        labels=labels,
        values=values,
        percentages=percentages
    )

@auth.route("/me")
def me():
    if 'user' not in session:
        return {"message":"Belum login"}, 401


    return {
        "id_user": session['user'],
        "nama": session['nama']
    }


@auth.route('/logout')
def logout():
    session.clear()
    return redirect('/')



