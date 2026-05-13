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
    return render_template('dashboard.html')

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