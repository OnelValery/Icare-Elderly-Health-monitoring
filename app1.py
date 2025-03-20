import sys
from flask import Flask, render_template, request, redirect, url_for, session
import db as db
import random
from db import db
from datetime import date
import pandas as pd
import numpy as np
import pyarrow as pa #to add Requirement
import os

# Create the Flask app
app = Flask(__name__)

# Set the secret key for session management (you can also use os.urandom(24) to generate a random secret key)
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24))


# Route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get data from the form
        role = request.form['role']  # 'patient', 'doctor', or 'caregiver'
        email = request.form['email']
        password = request.form['password']

        # Validate the user account based on the role
        if role == 'doctor':
            if db.valid_doctor_account(email, password):
                session['role'] = 'doctor'
                session['email'] = email
                return redirect(url_for('doctor'))  # Redirect to doctor dashboard after login
            else:
                return "Invalid email or password"
        elif role == 'patient':
            if db.valid_patient_account(email, password):
                session['role'] = 'patient'
                session['email'] = email
                return redirect(url_for('patient_dashboard'))  # Redirect to patient dashboard after login
            else:
                return "Invalid email or password"
        elif role == 'caregiver':
            if db.valid_caregiver_account(email, password):
                session['role'] = 'caregiver'
                session['email'] = email
                return redirect(url_for('caregiver_dashboard'))  # Redirect to caregiver dashboard after login
            else:
                return "Invalid email or password"

    return render_template('login.html')


# Route for doctor dashboard (after login)
@app.route('/doctor')
def doctor_dashboard():
    if 'role' not in session or session['role'] != 'doctor':
        return redirect(url_for('login'))  # Redirect to login if not logged in
    # Fetch doctor-specific data here, like doctor_id
    doctor_id = "D123"  # Example doctor ID
    return render_template('doctor_dashboard.html', doctor_id=doctor_id)


# Route for patient dashboard (after login)
@app.route('/patient-dashboard')
def patient_dashboard():
    if 'role' not in session or session['role'] != 'patient':
        return redirect(url_for('login'))  # Redirect to login if not logged in
    # Fetch patient-specific data here
    return render_template('patient_dashboard.html')


# Route for caregiver dashboard (after login)
@app.route('/caregiver-dashboard')
def caregiver_dashboard():
    if 'role' not in session or session['role'] != 'caregiver':
        return redirect(url_for('login'))  # Redirect to login if not logged in
    # Fetch caregiver-specific data here
    return render_template('caregiver_dashboard.html')


if __name__ == '__main__':
    app.run(debug=True)
