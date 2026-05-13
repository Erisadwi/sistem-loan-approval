from flask import Blueprint, render_template, request, redirect, session
from utils.db import get_db_connection
import bcrypt

auth = Blueprint('auth', __name__)


# LOGIN
@auth.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email'].strip()
        password = request.form['password'].strip()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:

            stored_password = user['password']

            if isinstance(stored_password, str):
                stored_password = stored_password.encode('utf-8')

            if bcrypt.checkpw(
                password.encode('utf-8'),
                stored_password
            ):

                session['user'] = user['id_user']
                session['nama'] = user['nama']

                return redirect('/dashboard')

            else:
                return "Password salah"

        else:
            return "User tidak ditemukan"

    return render_template('login.html')


# DATA USER
@auth.route('/me')
def me():

    if 'user' not in session:
        return {
            "message": "Belum login"
        }, 401

    return {
        "id_user": session['user'],
        "nama": session['nama']
    }


# LOGOUT
@auth.route('/logout')
def logout():

    session.clear()

    return redirect('/dashboard')