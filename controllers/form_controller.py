from flask import Blueprint, render_template, request, redirect, session
from utils.db import get_db_connection

from utils.activity_logger import catat_aktivitas

form_bp = Blueprint('form', __name__)

@form_bp.route('/', methods=['GET', 'POST'])
def form_pengajuan():

    if 'user' not in session:
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE id_user = %s",
        (session['user'],)
    )

    user = cursor.fetchone()

    if request.method == 'POST':

        no_of_dependents = request.form['no_of_dependents']
        self_employed = request.form['self_employed']
        income_annum = request.form['income_annum']
        loan_amount = request.form['loan_amount']
        loan_term = request.form['loan_term']
        cibil_score = request.form['cibil_score']

        query = """
        INSERT INTO pengajuan 
        (id_user, no_of_dependents, self_employed, income_annum, loan_amount, loan_term, cibil_score)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(query, (
            session['user'],
            no_of_dependents,
            self_employed,
            income_annum,
            loan_amount,
            loan_term,
            cibil_score
        ))

        conn.commit()

        id_pengajuan = cursor.lastrowid

        aktivitas = f"Membuat pengajuan pinjaman ID {id_pengajuan}"

        catat_aktivitas(
            conn,
            session['user'],
            aktivitas,
            "CREATE_PENGAJUAN",
            id_pengajuan
        )

        cursor.close()
        conn.close()

        return redirect('/hasil_analisis')

    cursor.close()
    conn.close()

    return render_template(
        'form_pengajuan.html',
        user=user
    )