from flask import Blueprint, render_template, request, redirect, session
from utils.db import get_db_connection
import os
import uuid

profil_bp = Blueprint('profil', __name__)

@profil_bp.route('/', methods=['GET', 'POST'])
def profil():

    if 'user' not in session:
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE id_user=%s", (session['user'],))
    user = cursor.fetchone()

    if request.method == 'POST':
        nama = request.form['nama']
        email = request.form['email']

        foto_filename = user['foto']

        file = request.files.get('foto')

        if file and file.filename != "":
            ext = file.filename.split('.')[-1]
            foto_filename = str(uuid.uuid4()) + "." + ext

            upload_path = os.path.join('static/uploads', foto_filename)
            file.save(upload_path)

        query = """
        UPDATE users 
        SET nama=%s, email=%s, foto=%s
        WHERE id_user=%s
        """

        cursor.execute(query, (nama, email, foto_filename, session['user']))
        conn.commit()

        cursor.close()
        conn.close()

        return redirect('/profil')

    if not user['foto']:
        user['foto'] = 'default.png'

    cursor.close()
    conn.close()

    return render_template('profil.html', user=user)