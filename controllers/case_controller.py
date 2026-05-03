from flask import Blueprint, render_template, request
from utils.db import get_db_connection

case = Blueprint('case', __name__)

@case.route('/case_base')
def case_base():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    per_page = 15
    
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * per_page

    cursor.execute("SELECT COUNT(*) as total FROM basis_kasus")
    total_data = cursor.fetchone()['total']
    total_pages = (total_data + per_page - 1) // per_page

    query = """
        SELECT 
            loan_id,
            no_of_dependents,
            self_employed,
            income_annum,
            loan_amount,
            loan_term,
            cibil_score,
            loan_status,
            tanggal_masuk
        FROM basis_kasus
        ORDER BY loan_id DESC
        LIMIT %s OFFSET %s
    """
    
    cursor.execute(query, (per_page, offset))
    data_kasus = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "case_base.html",
        kasus=data_kasus,
        page=page,
        total_pages=total_pages
    )