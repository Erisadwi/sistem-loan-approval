from flask import Flask, render_template
from controllers.auth_controller import auth
from config import Config
from controllers.form_controller import form_bp
from controllers.case_controller import case
from controllers.hasilAnalisis_controller import hasil_bp
from controllers.review_controller import review_bp
from controllers.profil_controller import profil_bp
from utils.db import get_db_connection

app = Flask(__name__)
app.config.from_object(Config)

# Register blueprint
app.register_blueprint(auth)
app.register_blueprint(form_bp, url_prefix='/form')
app.register_blueprint(case)
app.register_blueprint(hasil_bp)
app.register_blueprint(review_bp, url_prefix='/review')
app.register_blueprint(profil_bp, url_prefix='/profil')

# HALAMAN UTAMA
@app.route('/')
def home():
    return dashboard(dashboard.html)

# Dashboard
@app.route('/dashboard')
def dashboard():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # TOTAL DATA
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM basis_kasus
    """)
    total = cursor.fetchone()['total']

    # APPROVED
    cursor.execute("""
        SELECT COUNT(*) AS approved
        FROM basis_kasus
        WHERE loan_status='Approved'
    """)
    approved = cursor.fetchone()['approved']

    # REJECTED
    cursor.execute("""
        SELECT COUNT(*) AS rejected
        FROM basis_kasus
        WHERE loan_status='Rejected'
    """)
    rejected = cursor.fetchone()['rejected']

    # MENUNGGU
    pending = total - (approved + rejected)

    cursor.close()
    conn.close()

    return render_template(
        'dashboard.html',
        total=total,
        approved=approved,
        rejected=rejected,
        pending=pending
    )

# Review UI
@app.route("/review-ui")
def review_ui():
    return render_template("review.html")

# RIWAYAT
@app.route("/riwayat")
def riwayat():
    return render_template("riwayat.html")

if __name__ == '__main__':
    app.run(debug=True)