from flask import Blueprint, render_template, session, redirect, request
from utils.db import get_db_connection
import math
import random

hasil_bp = Blueprint('hasil', __name__)

# =========================
# MIN MAX
# =========================
def get_min_max(cursor, table, column):
    cursor.execute(f"SELECT MIN({column}) as min_val, MAX({column}) as max_val FROM {table}")
    result = cursor.fetchone()
    return float(result['min_val']), float(result['max_val'])

# =========================
# FUZZIFIKASI
# =========================
def fuzzifikasi_cibil(x, xmin, xmax):
    x = float(x)
    interval = (xmax - xmin) / 3

    a1 = xmin
    b1 = xmin + interval

    a2 = xmin + interval
    b2 = xmin + 2 * interval

    a3 = xmin + 2 * interval
    b3 = xmax

    rendah, sedang, tinggi = 0, 0, 0

    if a1 <= x <= b1:
        rendah = (b1 - x) / (b1 - a1)

    if a2 <= x <= b2:
        sedang = (x - a2) / (b2 - a2)
    elif b2 < x <= xmax:
        sedang = (xmax - x) / (xmax - b2)

    if a3 <= x <= b3:
        tinggi = (x - a3) / (b3 - a3)
    elif x > b3:
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
# DISTANCE
# =========================
def distance(a, b):
    return round(math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(len(a)))), 4)

# =========================
# K-MEANS
# =========================
def kmeans_indexed(data, k=3, max_iter=100):
    random.seed(42)
    centroids = random.sample(data, k)

    for _ in range(max_iter):
        clusters = [[] for _ in range(k)]

        for i, d in enumerate(data):
            distances = [distance(d, c) for c in centroids]
            idx = distances.index(min(distances))
            clusters[idx].append(i)

        new_centroids = []
        for cl in clusters:
            if cl:
                mean = [
                    sum(data[i][j] for i in cl) / len(cl)
                    for j in range(len(data[0]))
                ]
                new_centroids.append(mean)
            else:
                new_centroids.append(random.choice(data))

        if new_centroids == centroids:
            break

        centroids = new_centroids

    return clusters, centroids

# =========================
# ROUTE
# =========================
@hasil_bp.route('/hasil_analisis')
def hasil():

    if 'user' not in session:
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # =========================
    # DATA BARU
    # =========================
    cursor.execute("""
        SELECT * FROM pengajuan
        WHERE id_user=%s
        ORDER BY id_pengajuan DESC
        LIMIT 1
    """, (session['user'],))

    baru = cursor.fetchone()
    if not baru:
        return "Belum ada data"

    # =========================
    # MIN MAX
    # =========================
    dep_min, dep_max = get_min_max(cursor, 'basis_kasus', 'no_of_dependents')
    income_min, income_max = get_min_max(cursor, 'basis_kasus', 'income_annum')
    loan_min, loan_max = get_min_max(cursor, 'basis_kasus', 'loan_amount')
    term_min, term_max = get_min_max(cursor, 'basis_kasus', 'loan_term')
    cibil_min, cibil_max = get_min_max(cursor, 'basis_kasus', 'cibil_score')

    # =========================
    # FUZZY
    # =========================
    kategori, rendah, sedang, tinggi, _ = fuzzifikasi_cibil(
        baru['cibil_score'], cibil_min, cibil_max
    )

    # =========================
    # NORMALISASI BARU
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
    # DATA LAMA
    # =========================
    cursor.execute("SELECT * FROM basis_kasus")
    kasus_lama = cursor.fetchall()

    data_norm = []
    meta = []

    for d in kasus_lama:
        vec = [
            norm(d['no_of_dependents'], dep_min, dep_max),
            1 if str(d['self_employed']).lower() == "yes" else 0,
            norm(d['income_annum'], income_min, income_max),
            norm(d['loan_amount'], loan_min, loan_max),
            norm(d['loan_term'], term_min, term_max),
            norm(d['cibil_score'], cibil_min, cibil_max)
        ]

        data_norm.append(vec)
        meta.append({
            'loan_id': d['loan_id'],
            'keputusan': str(d['loan_status']).capitalize()
        })

    # =========================
    # KMEANS
    # =========================
    clusters, centroids = kmeans_indexed(data_norm, k=3)

    # LABEL CLUSTER BERDASARKAN CIBIL
    centroid_cibil = [c[5] for c in centroids]
    sorted_idx = sorted(range(len(centroid_cibil)), key=lambda i: centroid_cibil[i])

    label_map = {
        sorted_idx[0]: "Kategori Rendah",
        sorted_idx[1]: "Kategori Sedang",
        sorted_idx[2]: "Kategori Tinggi"
    }

    # PILIH CLUSTER
    dist_centroid = [distance(baru_norm, c) for c in centroids]
    cluster_terdekat = dist_centroid.index(min(dist_centroid))
    cluster_label = label_map[cluster_terdekat]

    # =========================
    # DATA CLUSTER
    # =========================
    cluster_idx = clusters[cluster_terdekat]

    cluster_data = []
    for i in cluster_idx:
        dist = distance(baru_norm, data_norm[i])

        cluster_data.append({
            'id_kasus': meta[i]['loan_id'],
            'distance': dist,
            'keputusan': meta[i]['keputusan']
        })

    # =========================
    # SIMILARITY
    # =========================
    distances = [x['distance'] for x in cluster_data]
    dmin, dmax = min(distances), max(distances)

    for x in cluster_data:
        x['similarity'] = 1 if dmax == dmin else round(1 - ((x['distance'] - dmin)/(dmax - dmin)),4)

    # =========================
    # KNN WEIGHTED + FUZZY
    # =========================
    n_cluster = len(cluster_data)
    k_val = max(1, int(math.sqrt(n_cluster)))
    if k_val % 2 == 0:
        k_val += 1

    cluster_data = sorted(cluster_data, key=lambda x: x['distance'])
    topk = cluster_data[:k_val]

    score_approved = 0
    score_rejected = 0

    fuzzy_weight = tinggi if kategori=="Tinggi" else sedang if kategori=="Sedang" else rendah

    for x in topk:
        w = x['similarity'] * fuzzy_weight
        if x['keputusan']=="Approved":
            score_approved += w
        else:
            score_rejected += w

    mdm_approved = None
    mdm_rejected = None

    if score_approved > score_rejected:
        keputusan = "Approved"
    elif score_rejected > score_approved:
        keputusan = "Rejected"
    else:
        jarak_approved = [x['distance'] for x in topk if x['keputusan']=="Approved"]
        jarak_rejected = [x['distance'] for x in topk if x['keputusan']=="Rejected"]

        mdm_approved = sum(jarak_approved)/len(jarak_approved) if jarak_approved else float('inf')
        mdm_rejected = sum(jarak_rejected)/len(jarak_rejected) if jarak_rejected else float('inf')

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

    # =========================
    # RETURN
    # =========================
    return render_template(
        'hasil_analisis.html',
        matriks=matriks,
        topk=topk,
        keputusan=keputusan,
        k=k_val,
        n_cluster=n_cluster,
        cluster_label=cluster_label,
        approved=sum(1 for x in topk if x['keputusan']=="Approved"),
        rejected=sum(1 for x in topk if x['keputusan']=="Rejected"),
        kategori_cibil=kategori,
        nilai_rendah=rendah,
        nilai_sedang=sedang,
        nilai_tinggi=tinggi,
        mdm_approved=round(mdm_approved,4) if mdm_approved else None,
        mdm_rejected=round(mdm_rejected,4) if mdm_rejected else None
    )