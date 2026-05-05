from flask import Blueprint, render_template, request, session, url_for, jsonify
from utils.db import get_db_connection

case = Blueprint('case', __name__)

@case.route('/case_base')
def case_base():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    per_page = 15
    
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * per_page

    search_id = request.args.get('search_id', '')
    status = request.args.get('status', '')

    count_query = "SELECT COUNT(*) as total FROM basis_kasus WHERE 1=1"
    count_params = []

    if search_id:
        count_query += " AND loan_id LIKE %s"
        count_params.append(f"%{search_id}%")

    if status:
        count_query += " AND loan_status = %s"
        count_params.append(status)

    cursor.execute(count_query, count_params)
    total_data = cursor.fetchone()['total']

    total_pages = (total_data + per_page - 1) // per_page

    data_query = """
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
        WHERE 1=1
    """

    data_params = []

    if search_id:
        data_query += " AND loan_id LIKE %s"
        data_params.append(f"%{search_id}%")

    if status:
        data_query += " AND loan_status = %s"
        data_params.append(status)

    data_query += " ORDER BY loan_id DESC LIMIT %s OFFSET %s"
    data_params.extend([per_page, offset])

    cursor.execute(data_query, data_params)
    data_kasus = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "case_base.html",
        kasus=data_kasus,
        page=page,
        total_pages=total_pages
    )