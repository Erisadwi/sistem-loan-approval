from flask import Blueprint, render_template, request, redirect, session
from utils.db import get_db_connection

form_bp = Blueprint('form', __name__)

@form_bp.route('/', methods=['GET', 'POST'])
def form_pengajuan():
    
    if 'user' not in session:
        return redirect('/')

    if request.method == 'POST':
        no_of_dependents = request.form['no_of_dependents']
        self_employed = request.form['self_employed']
        income_annum = request.form['income_annum']
        loan_amount = request.form['loan_amount']
        loan_term = request.form['loan_term']
        cibil_score = request.form['cibil_score']

        conn = get_db_connection()
        cursor = conn.cursor()

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
        cursor.close()
        conn.close()

        return redirect('/hasil_analisis')

    return render_template('form_pengajuan.html')