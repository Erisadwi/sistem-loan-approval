from flask import Blueprint, render_template, session, redirect, request
from utils.db import get_db_connection
import math

hasil_bp = Blueprint('hasil', __name__)

# =========================
# AMBIL MIN MAX DARI DB
# =========================
def get_min_max(cursor, table, column):
    cursor.execute(f"SELECT MIN({column}) as min_val, MAX({column}) as max_val FROM {table}")
    result = cursor.fetchone()
    return float(result['min_val']), float(result['max_val'])

# =========================
# FUZZIFIKASI CIBIL
# =========================
def fuzzifikasi_cibil(x, xmin, xmax):

    x = float(x)

    range_val = xmax - xmin
    interval = range_val / 3

    a1 = xmin
    b1 = xmin + interval
    c1 = xmin + 2 * interval

    a2 = xmin + interval
    b2 = xmin + 2 * interval
    c2 = xmax

    a3 = xmin + 2 * interval
    b3 = xmax
    c3 = xmax

    rendah = 0
    sedang = 0
    tinggi = 0

    if a1 <= x <= b1:
        rendah = (b1 - x) / (b1 - a1)

    if a2 <= x <= c2:
        if x <= b2:
            sedang = (x - a2) / (b2 - a2)
        else:
            sedang = (c2 - x) / (c2 - b2)

    if a3 <= x <= c3:
        if x <= b3:
            tinggi = (x - a3) / (b3 - a3)
        else:
            tinggi = 1

    nilai = {
        "Rendah": rendah,
        "Sedang": sedang,
        "Tinggi": tinggi
    }

    kategori = max(nilai, key=nilai.get)

    return kategori, round(rendah,4), round(sedang,4), round(tinggi,4), interval

# =========================
# NORMALISASI
# =========================
def norm(val, min_val, max_val):
    if max_val == min_val:
        return 0
    return (float(val) - float(min_val)) / (float(max_val) - float(min_val))

# =========================
# EUCLIDEAN DISTANCE
# =========================
def distance(a, b):
    return round(math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(len(a)))), 4)

# =========================
# ROUTE HASIL ANALISIS
# =========================
@hasil_bp.route('/hasil_analisis')
def hasil():

    if 'user' not in session:
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # =========================
    # 🔥 FIX: AMBIL ID DARI URL
    # =========================
    id_pengajuan = request.args.get('id')

    if id_pengajuan:
        cursor.execute("""
            SELECT * FROM pengajuan
            WHERE id_pengajuan=%s
        """, (id_pengajuan,))
    else:
        cursor.execute("""
            SELECT * FROM pengajuan
            WHERE id_user=%s
            ORDER BY id_pengajuan DESC
            LIMIT 1
        """, (session['user'],))

    baru = cursor.fetchone()

    if not baru:
        return "Belum ada data pengajuan"

    # =========================
    # MIN MAX DINAMIS
    # =========================
    dep_min, dep_max = get_min_max(cursor, 'basis_kasus', 'no_of_dependents')
    income_min, income_max = get_min_max(cursor, 'basis_kasus', 'income_annum')
    loan_min, loan_max = get_min_max(cursor, 'basis_kasus', 'loan_amount')
    term_min, term_max = get_min_max(cursor, 'basis_kasus', 'loan_term')
    cibil_min, cibil_max = get_min_max(cursor, 'basis_kasus', 'cibil_score')

    # =========================
    # FUZZIFIKASI
    # =========================
    kategori, rendah, sedang, tinggi, interval = fuzzifikasi_cibil(
        baru['cibil_score'],
        cibil_min,
        cibil_max
    )

    # =========================
    # NORMALISASI DATA BARU
    # =========================
    baru_norm = [
        norm(baru['no_of_dependents'], dep_min, dep_max),
        1 if str(baru['self_employed']).lower() == "yes" else 0,
        norm(baru['income_annum'], income_min, income_max),
        norm(baru['loan_amount'], loan_min, loan_max),
        norm(baru['loan_term'], term_min, term_max),
        norm(baru['cibil_score'], cibil_min, cibil_max)
    ]

    matriks = [{
        'id_pengajuan': baru['id_pengajuan'],
        'no_of_dependents': round(baru_norm[0], 4),
        'self_employed': baru_norm[1],
        'income_annum': round(baru_norm[2], 4),
        'loan_amount': round(baru_norm[3], 4),
        'loan_term': round(baru_norm[4], 4),
        'cibil_score': round(baru_norm[5], 4)
    }]

    # =========================
    # DATA KASUS LAMA
    # =========================
    cursor.execute("SELECT * FROM basis_kasus")
    kasus_lama = cursor.fetchall()

    if not kasus_lama:
        return "Data kasus lama kosong"

    hasil = []

    for k in kasus_lama:
        lama_norm = [
            norm(k['no_of_dependents'], dep_min, dep_max),
            1 if str(k['self_employed']).lower() == "yes" else 0,
            norm(k['income_annum'], income_min, income_max),
            norm(k['loan_amount'], loan_min, loan_max),
            norm(k['loan_term'], term_min, term_max),
            norm(k['cibil_score'], cibil_min, cibil_max)
        ]

        d = distance(baru_norm, lama_norm)

        hasil.append({
            'id_kasus': k['loan_id'],
            'distance': d,
            'keputusan': str(k['loan_status']).capitalize()
        })

    # =========================
    # SIMILARITY
    # =========================
    all_dist = [x['distance'] for x in hasil]
    dmin = min(all_dist)
    dmax = max(all_dist)

    for x in hasil:
        if dmax == dmin:
            x['similarity'] = 1
        else:
            sim = 1 - ((x['distance'] - dmin) / (dmax - dmin))
            x['similarity'] = round(sim, 4)

    # =========================
    # SORTING
    # =========================
    hasil = sorted(hasil, key=lambda x: x['distance'])

    # =========================
    # KNN
    # =========================
    n = len(hasil)
    k_val = max(1, int(math.sqrt(n)))

    if k_val % 2 == 0:
        k_val += 1

    topk = hasil[:k_val]

    approved = sum(1 for x in topk if x['keputusan'] == "Approved")
    rejected = sum(1 for x in topk if x['keputusan'] == "Rejected")

    mdm_approved = None
    mdm_rejected = None

    if approved > rejected:
        keputusan = "Approved"
    elif rejected > approved:
        keputusan = "Rejected"
    else:
        jarak_approved = [x['distance'] for x in topk if x['keputusan'] == "Approved"]
        jarak_rejected = [x['distance'] for x in topk if x['keputusan'] == "Rejected"]

        mdm_approved = sum(jarak_approved) / len(jarak_approved) if jarak_approved else float('inf')
        mdm_rejected = sum(jarak_rejected) / len(jarak_rejected) if jarak_rejected else float('inf')

        keputusan = "Approved" if mdm_approved < mdm_rejected else "Rejected"

    # =========================
    # CEK APAKAH SUDAH PERNAH DIREVIEW
    # =========================
    cursor.execute("""
        SELECT id_review FROM review_analis
        WHERE id_pengajuan=%s
    """, (baru['id_pengajuan'],))

    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO review_analis (id_pengajuan, keputusan)
            VALUES (%s, %s)
        """, (baru['id_pengajuan'], keputusan))

    conn.commit()
    cursor.close()
    conn.close()

    return render_template(
        'hasil_analisis.html',
        matriks=matriks,
        topk=topk,
        keputusan=keputusan,
        k=k_val,
        n=n,
        kategori_cibil=kategori,
        nilai_sedang=sedang,
        nilai_tinggi=tinggi,
        approved=approved,
        rejected=rejected,
        mdm_approved=round(mdm_approved, 4) if mdm_approved else None,
        mdm_rejected=round(mdm_rejected, 4) if mdm_rejected else None
    )