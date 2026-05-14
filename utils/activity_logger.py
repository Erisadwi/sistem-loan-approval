from datetime import datetime

def catat_aktivitas(conn, id_user, aktivitas, jenis, id_pengajuan=None):
    cursor = conn.cursor()

    query = """
        INSERT INTO log_activity
        (id_user, aktivitas, jenis_aktivitas, waktu, id_pengajuan)
        VALUES (%s,%s,%s,%s,%s)
    """

    cursor.execute(query, (
        id_user,
        aktivitas,
        jenis,
        datetime.now(),
        id_pengajuan
    ))

    conn.commit()