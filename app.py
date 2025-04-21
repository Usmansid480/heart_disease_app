from flask import Flask, render_template, request
import joblib
import numpy as np

app = Flask(__name__)

# Load your trained model once at startup
model = joblib.load('models/heart_model.joblib')

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/form')
def form():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    # Gather inputs from the form
    features = [
        int(request.form['age']),
        int(request.form['sex']),
        int(request.form['cp']),
        int(request.form['trestbps']),
        int(request.form['chol']),
        int(request.form['fbs']),
        int(request.form['restecg']),
        int(request.form['thalach']),
        int(request.form['exang']),
        float(request.form['oldpeak']),
        int(request.form['slope'])
    ]

    # Run prediction
    pred = model.predict([features])[0]

    # Choose result text and recommendation
    if pred == 1:
        result_text = "⚠️ High risk of heart disease detected."
        recommendation = "🩺 Please consult a cardiologist immediately."
    else:
        result_text = "✅ Low risk of heart disease."
        recommendation = "💡 Maintain a healthy lifestyle and regular check‑ups."

    # Render the result page
    return render_template('result.html',
                           prediction=result_text,
                           recommendation=recommendation)

# Expose manifest and service worker for PWA
@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

@app.route('/service-worker.js')
def sw():
    return app.send_static_file('service-worker.js')

if __name__ == '__main__':
    app.run(debug=True)
