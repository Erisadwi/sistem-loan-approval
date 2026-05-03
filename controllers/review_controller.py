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

    if "user" not in session:
        return jsonify({"message":"Belum login"}),401

    db = get_db()
    cursor = db.cursor(dictionary=True)

    query = """
    SELECT 
        p.id_pengajuan,
        p.no_of_dependents,
        p.self_employed,
        p.income_annum,
        p.loan_amount,
        p.loan_term,
        p.cibil_score,
        p.status_proses,
        r.keputusan,
        r.catatan,
        r.tanggal_review
    FROM pengajuan p
    LEFT JOIN review_analis r 
        ON p.id_pengajuan = r.id_pengajuan
    WHERE p.status_proses IN ('MENUNGGU_REVIEW','DIREVIEW')
    ORDER BY p.id_pengajuan DESC
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

    cursor.execute("""
        UPDATE pengajuan
        SET status_proses='DIREVIEW'
        WHERE id_pengajuan=%s
    """,(id_pengajuan,))

    db.commit()

    return jsonify({"message":"Revisi berhasil"})

def generate_loan_id(cursor):
    cursor.execute("""
        SELECT loan_id 
        FROM basis_kasus 
        ORDER BY loan_id DESC 
        LIMIT 1
    """)
    last = cursor.fetchone()

    if not last:
        return "LID0001"

    last_id = last["loan_id"]     
    number = int(last_id[3:]) + 1  
    return f"LID{number:04d}"


@review_bp.route("/retain/<int:id_pengajuan>", methods=["POST"])
def retain_case(id_pengajuan):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
    SELECT 
        p.id_pengajuan,
        p.no_of_dependents,
        p.self_employed,
        p.income_annum,
        p.loan_amount,
        p.loan_term,
        p.cibil_score,
        r.id_analis,
        r.keputusan
    FROM pengajuan p
    JOIN review_analis r ON p.id_pengajuan=r.id_pengajuan
    WHERE p.id_pengajuan=%s
    """,(id_pengajuan,))
    
    kasus = cursor.fetchone()


    if not kasus:
        return jsonify({
            "error":"Pengajuan belum direview analis!"
        }), 400

    loan_id = generate_loan_id(cursor)

    cursor.execute("""
    INSERT INTO basis_kasus
    (loan_id, id_pengajuan, id_analis,
     no_of_dependents, self_employed, income_annum,
     loan_amount, loan_term, cibil_score, loan_status)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """,(
        loan_id,
        kasus["id_pengajuan"],   
        kasus["id_analis"],      
        kasus["no_of_dependents"],
        kasus["self_employed"],
        kasus["income_annum"],
        kasus["loan_amount"],
        kasus["loan_term"],
        kasus["cibil_score"],
        kasus["keputusan"]
    ))

    cursor.execute("""
        UPDATE pengajuan
        SET status_proses='SELESAI'
        WHERE id_pengajuan=%s
    """,(id_pengajuan,))
    
    db.commit()
    return jsonify({
        "message": "Kasus berhasil disimpan ke basis kasus",
        "loan_id_baru": loan_id
    })