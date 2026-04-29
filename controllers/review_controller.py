import mysql.connector
from flask import Blueprint, request, jsonify, session

review_bp = Blueprint("review", __name__)

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="loan_data"
    )

@review_bp.route("/pending", methods=["GET"])
def get_data_review():

    # 🔐 wajib login dulu
    if "user" not in session:
        return jsonify({"message":"Belum login"}),401

    db = get_db()
    cursor = db.cursor(dictionary=True)

    query = """
    SELECT 
        r.id_pengajuan,
        r.keputusan,
        r.catatan,
        r.tanggal_review,
        p.income_annum,
        p.loan_amount,
        p.cibil_score
    FROM review_analis r
    JOIN pengajuan p ON r.id_pengajuan = p.id_pengajuan
    ORDER BY r.tanggal_review DESC
    """

    cursor.execute(query)
    data = cursor.fetchall()

    return jsonify({"data":data})

@review_bp.route("/revise/<int:id_pengajuan>", methods=["PUT"])
def revise_keputusan(id_pengajuan):
    db = get_db()
    cursor = db.cursor()

    data = request.json
    keputusan = data.get("keputusan")
    catatan = data.get("catatan","")

    query = """
    UPDATE review_analis
    SET keputusan=%s, catatan=%s, tanggal_review=NOW()
    WHERE id_pengajuan=%s
    """
    cursor.execute(query,(keputusan,catatan,id_pengajuan))
    db.commit()

    return jsonify({"message":"Revisi berhasil"})

def generate_loan_id(cursor):
    cursor.execute("SELECT COUNT(*) FROM basis_kasus")
    count = cursor.fetchone()[0] + 1
    return f"LID{count:04d}"

@review_bp.route("/retain/<int:id_pengajuan>", methods=["POST"])
def retain_case(id_pengajuan):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
    SELECT 
        p.no_of_dependents,
        p.self_employed,
        p.income_annum,
        p.loan_amount,
        p.loan_term,
        p.cibil_score,
        r.keputusan
    FROM pengajuan p
    JOIN review_analis r ON p.id_pengajuan=r.id_pengajuan
    WHERE p.id_pengajuan=%s
    """,(id_pengajuan,))
    
    kasus = cursor.fetchone()
    loan_id = generate_loan_id(cursor)

    cursor.execute("""
    INSERT INTO basis_kasus
    (loan_id,no_of_dependents,self_employed,income_annum,
     loan_amount,loan_term,cibil_score,loan_status)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """,(
        loan_id,
        kasus["no_of_dependents"],
        kasus["self_employed"],
        kasus["income_annum"],
        kasus["loan_amount"],
        kasus["loan_term"],
        kasus["cibil_score"],
        kasus["keputusan"]
    ))

    db.commit()
    return jsonify({"loan_id_baru":loan_id})