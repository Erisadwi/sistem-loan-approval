from flask import Blueprint, render_template, session, redirect
from utils.db import get_db_connection
import math

hasil_bp = Blueprint('hasil', __name__)

# =========================
# FUZZIFIKASI CIBIL
# =========================
def fuzzifikasi_cibil(x):
    x = float(x)

    sedang = 0
    tinggi = 0

    if 500 <= x <= 700:
        if x <= 600:
            sedang = (x - 500) / 100
        else:
            sedang = (700 - x) / 100

    if 600 <= x <= 861:
        if x <= 700:
            tinggi = (x - 600) / 100
        else:
            tinggi = (861 - x) / 200

    kategori = "tinggi" if tinggi > sedang else "sedang"

    return kategori, round(sedang, 4), round(tinggi, 4)


# =========================
# NORMALISASI
# =========================
def norm(val, min_val, max_val):
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
    # 1. AMBIL KASUS BARU (FORM)
    # =========================
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
    # 2. FUZZIFIKASI
    # =========================
    kategori, sedang, tinggi = fuzzifikasi_cibil(baru['cibil_score'])

    # =========================
    # 3. AMBIL KASUS LAMA
    # =========================
    cursor.execute("SELECT * FROM basis_kasus")
    kasus_lama = cursor.fetchall()

    if not kasus_lama:
        return "Data kasus lama kosong"

    # =========================
    # 4. NORMALISASI DATA BARU
    # =========================
    baru_norm = [
        norm(baru['no_of_dependents'], 0, 5),
        1 if baru['self_employed'] == "Yes" else 0,
        norm(baru['income_annum'], 300000, 9900000),
        norm(baru['loan_amount'], 900000, 37600000),
        norm(baru['loan_term'], 2, 20),
        norm(baru['cibil_score'], 300, 861)
    ]

    hasil = []

    # =========================
    # 5. HITUNG DISTANCE
    # =========================
    matriks = []
    for k in kasus_lama:

        lama_norm = [
            norm(k['no_of_dependents'], 0, 5),
            1 if k['self_employed'] == "Yes" else 0,
            norm(k['income_annum'], 300000, 9900000),
            norm(k['loan_amount'], 900000, 37600000),
            norm(k['loan_term'], 2, 20),
            norm(k['cibil_score'], 300, 861)
        ]

        matriks.append({
            'id_kasus': k['loan_id'],
            'no_of_dependents': round(lama_norm[0], 4),
            'self_employed': lama_norm[1],
            'income_annum': round(lama_norm[2], 4),
            'loan_amount': round(lama_norm[3], 4),
            'loan_term': round(lama_norm[4], 4),
            'cibil_score': round(lama_norm[5], 4)
        })

        d = distance(baru_norm, lama_norm)

        hasil.append({
            'id_kasus': k['loan_id'],
            'distance': d,
            'keputusan': k['loan_status']  # approved / rejected
        })

    # =========================
    # 6. HITUNG SIMILARITY
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
    # 7. SORTING (RANKING)
    # =========================
    hasil = sorted(hasil, key=lambda x: x['similarity'], reverse=True)

    # =========================
    # 8. KNN
    # =========================
    n = len(hasil)
    k_val = max(1, int(math.sqrt(n)))

    topk = hasil[:k_val]

    approved = sum(1 for x in topk if x['keputusan'] == "Approved")
    rejected = sum(1 for x in topk if x['keputusan'] == "Rejected")

    mdm_approved = None
    mdm_rejected = None

    # =========================
    # 9. KEPUTUSAN
    # =========================
    if approved > rejected:
        keputusan = "Approved"

    elif rejected > approved:
        keputusan = "Rejected"

    else:
        # ===== TIE → MDM =====
        jarak_approved = [x['distance'] for x in topk if x['keputusan'] == "approved"]
        jarak_rejected = [x['distance'] for x in topk if x['keputusan'] == "rejected"]

        mdm_approved = sum(jarak_approved) / len(jarak_approved) if jarak_approved else float('inf')
        mdm_rejected = sum(jarak_rejected) / len(jarak_rejected) if jarak_rejected else float('inf')

        # pilih jarak TERKECIL
        if mdm_approved < mdm_rejected:
            keputusan = "Approve"
        else:
            keputusan = "Rejected"

    # =========================
    # 10. SIMPAN KE DATABASE
    # =========================
    cursor.execute("""
        INSERT INTO review_analis (id_pengajuan, keputusan)
        VALUES (%s, %s)
    """, (baru['id_pengajuan'], keputusan))

    conn.commit()

    cursor.close()
    conn.close()

    # =========================
    # 11. TAMPILKAN KE HTML
    # =========================
    return render_template(
        'hasil_analisis.html',
        matriks=matriks,
        ranking=hasil,
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