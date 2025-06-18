from flask import Flask, render_template, request, redirect, url_for, session, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import joblib
import numpy as np
from io import BytesIO
from reportlab.pdfgen import canvas

# ========== App Configuration ==========
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# ========== Database Configuration ==========
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ========== Models ==========
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    scans = db.relationship('Scan', backref='user', lazy=True)

class Scan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    prediction = db.Column(db.String(100))
    input_data = db.Column(db.String(500))
    date = db.Column(db.DateTime, default=datetime.utcnow)

# ========== Load ML Model & Scaler ==========
model = joblib.load('models/heart_model.joblib')
scaler = joblib.load('models/scaler.joblib')

# ========== Routes ==========
@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/form')
def form():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = [
            int(request.form.get('age')),
            int(request.form.get('sex')),
            int(request.form.get('cp')),
            int(request.form.get('trestbps')),
            int(request.form.get('chol')),
            int(request.form.get('fbs')),
            int(request.form.get('restecg')),
            int(request.form.get('thalach')),
            int(request.form.get('exang')),
            float(request.form.get('oldpeak')),
            int(request.form.get('slope'))
        ]

        scaled_data = scaler.transform([data])
        prediction = model.predict(scaled_data)[0]

        if prediction == 1:
            status = "⚠️ High risk of heart disease detected."
            recommendation = """
            <ul>
                <li>📋 Schedule an <strong>ECG, cholesterol test</strong>, and <strong>stress test</strong>.</li>
                <li>👨‍⚕️ Consult a <strong>Cardiologist</strong> immediately.</li>
                <li>🥗 Start a <strong>heart-healthy diet</strong>.</li>
                <li>🚶‍♂️ Begin light activity under supervision.</li>
                <li>💊 Monitor blood pressure and sugar levels.</li>
            </ul>
            <h3>🏥 Recommended Cardiologists in Delhi:</h3>
            <ul>
                <li>Dr. Ashok Seth – Fortis Escorts Heart Institute</li>
                <li>Dr. Naresh Trehan – Medanta The Medicity</li>
                <li>Dr. Balbir Singh – Max Super Speciality Hospital</li>
            </ul>
            <h3>🏥 Hospitals:</h3>
            <ul>
                <li>Fortis Escorts, Okhla</li>
                <li>Medanta – The Medicity, Gurgaon</li>
                <li>Max Super Speciality Hospital, Saket</li>
                <li>AIIMS, Delhi</li>
            </ul>
            """
        else:
            status = "✅ Low risk of heart disease."
            recommendation = """
            <ul>
                <li>🩺 Maintain annual checkups.</li>
                <li>🥗 Eat a balanced diet.</li>
                <li>🚴‍♂️ Exercise regularly.</li>
                <li>🧘‍♀️ Manage stress with yoga or meditation.</li>
            </ul>
            <h3>📍 Optional Cardiologists:</h3>
            <ul>
                <li>Dr. Viveka Kumar – Max Hospital</li>
                <li>Dr. T. S. Kler – Fortis Hospital</li>
            </ul>
            """

        scan_id = None
        if 'user_id' in session:
            scan = Scan(user_id=session['user_id'], prediction=status, input_data=str(data))
            db.session.add(scan)
            db.session.commit()
            scan_id = scan.id

        return render_template('result.html', status=status, recommendation=recommendation, scan_id=scan_id)

    except Exception as e:
        return f"❌ Error occurred: {e}"

@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    scans = Scan.query.filter_by(user_id=session['user_id']).all()
    return render_template('history.html', history=scans)

@app.route('/download_report/<int:scan_id>')
def download_report(scan_id):
    scan = Scan.query.get(scan_id)
    if not scan or scan.user_id != session.get('user_id'):
        return "❌ Access denied."

    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 800, "Heart Predict AI - Scan Report")
    p.setFont("Helvetica", 12)
    p.drawString(100, 760, f"Date: {scan.date.strftime('%Y-%m-%d %H:%M:%S')}")
    p.drawString(100, 740, f"Prediction: {scan.prediction}")
    p.drawString(100, 720, f"Input Data: {scan.input_data}")
    p.drawString(100, 680, "Recommendations: See app for full details.")
    p.showPage()
    p.save()
    buffer.seek(0)

    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=report_{scan_id}.pdf'
    return response

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            return "❌ Username already exists."
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(
            username=request.form['username'],
            password=request.form['password']
        ).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('form'))
        return "❌ Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))

# ========== Initialize DB ==========
with app.app_context():
    db.create_all()

# ========== Run ==========
if __name__ == '__main__':
    app.run(debug=True)
