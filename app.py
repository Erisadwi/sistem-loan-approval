from flask import Flask, render_template
from controllers.auth_controller import auth
from config import Config
from controllers.form_controller import form_bp
from controllers.case_controller import case
from controllers.hasilAnalisis_controller import hasil_bp
from controllers.review_controller import review_bp

app = Flask(__name__)
app.config.from_object(Config)

app.register_blueprint(auth)
app.register_blueprint(form_bp, url_prefix='/form')
app.register_blueprint(case)
app.register_blueprint(hasil_bp)
app.register_blueprint(review_bp, url_prefix='/review')

@app.route("/review-ui")
def review_ui():
    return render_template("review.html")

if __name__ == '__main__':
    app.run(debug=True)