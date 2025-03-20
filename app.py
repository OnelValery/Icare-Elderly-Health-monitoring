import sys
from flask import Flask,flash, render_template, request, redirect, url_for, session
import db as db
import random
from db import db
from datetime import date
import pandas as pd
import numpy as np
import pyarrow as pa #to add Requirement
import os

app = Flask(__name__, template_folder='templates', static_folder='static')

# Set the secret key for session management (you can also use os.urandom(24) to generate a random secret key)
app.secret_key = os.getenv('SECRET_KEY', 'cd9afe475513d33562368a0218154fd066fef8e59c28036fdd368a8eb6cd448d')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get data from the form
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        phone_number = request.form['phone_number']
        email = request.form['email']
        password = request.form['password']
        address = request.form['address']
        role = request.form['role']  # 'patient', 'doctor', or 'responsible_person'

        # Add user to the database
        if role=='doctor':
            doctor_id='0000000'
            if db.register_doctor(doctor_id,firstname, lastname, phone_number, email, password, address):
                return redirect(url_for('login'))  # Redirect to login page after successful registration
            else:
                return "Error occurred while registering. Please try again."
        elif role=='patient':
            patient_id='0000000000'
            if db.register_patient(patient_id,firstname, lastname, phone_number, email, password, address):
                return redirect(url_for('login'))  # Redirect to login page after successful registration
            else:
                return "Error occurred while registering. Please try again."
        elif role=='caregiver':
            caregiver_id='0000000'
            if db.register_caregiver(caregiver_id,firstname, lastname, phone_number, email, password, address):
                return redirect(url_for('login'))  # Redirect to login page after successful registration
            else:
                return "Error occurred while registering. Please try again."


    return render_template('register.html')


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
                session['role']=role
                session['email']=email
                return redirect(url_for('doctor'))  # Redirect to doctor dashboard after login
            else:
                return "Invalid email or password"
        elif role == 'patient':
            if db.valid_patient_account(email, password):
                session['role'] = role
                session['email'] = email
                return redirect(url_for('patient'))  # Redirect to patient dashboard after login
            else:
                return "Invalid email or password"
        elif role == 'caregiver':
            if db.valid_caregiver_account(email, password):
                session['role'] = role
                session['email'] = email
                return redirect(url_for('caregiver'))  # Redirect to caregiver dashboard after login
            else:
                return "Invalid email or password"

    return render_template('login.html')

@app.route('/doctor', methods=['GET', 'POST'])
def doctor():
    if 'role' not in session or session['role'] != 'doctor':
        return redirect(url_for('login'))  # Redirect to login if not logged in

    email = session.get('email')
    doctor_id = db.get_doctor_id_by_email(email)
    doctor_data = db.get_doctor_data(doctor_id)
    doctor_data_dict = {
        'id': doctor_data[0],
        'first_name': doctor_data[1],
        'last_name': doctor_data[2],
        'email': doctor_data[3],
        'address': doctor_data[6],
        'phone_number': doctor_data[5]
    }
    
     # Formulaire pour ajouter un patient
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')

        # Si le médecin veut ajouter un patient
        if patient_id and 'remove_patient' not in request.form:
            # Check if the patient exists
            new_patient = db.get_patient_by_id(patient_id)
    
            if new_patient:
            # Check if the doctor_id of the patient is NULL (i.e., the patient is not assigned to any doctor)
                if new_patient[7] is None:  # Assuming new_patient is a dictionary or result object
            # Add the patient to the doctor's list by associating the doctor_id to the patient
                    if db.doctor_Add_patient(doctor_id,patient_id):
                        flash(f"Patient {new_patient[1]} {new_patient[2]} has been added to your list.", "success")
                    else:
                        flash("Error adding the patient to your list.", "error")
                else:
                # If the doctor_id is not NULL, do not add the patient and show a message
                    flash("This patient cannot be followed by multiple doctors.", "error")
            else:
                flash("This patient does not exist in the database.", "error")


        # Si le médecin veut supprimer un patient
        elif 'remove_patient' in request.form:
            patient_id_to_remove = request.form.get('patient_id')
           
            if db.remove_doctor_for_patient(doctor_id,patient_id_to_remove):
                # Supprimer le patient de la base de données
                
                flash(f"Patient {patient_id_to_remove} has been removed.", "success")
            else:
                flash(f"Patient {patient_id_to_remove} does not exist.", "error")

    
        # Vérifier si le patient existe dans la base de données
        
    patients=[]
    new_patient={}
    patient_data = db.get_the_doctor_patients(doctor_id)
    if patient_data is None:
        flash("Error fetching patients. Please try again later.", "error")
        return render_template('doctor.html', doctor_data_dict=doctor_data_dict, patient_data=[])
    else:
        for data_patient in  patient_data:
            new_patient = {
                'patient_id': data_patient[0],
                'first_name': data_patient[1],
                'last_name': data_patient[2],
                'phone_number': data_patient[5],
                'patient_email':data_patient[3],
                'patient_adress':data_patient[6],
                'caregiver_tasks': [],
                'patient_tasks': []
            }
        patients.append(new_patient)

            # Ajoutez le patient à une liste (par exemple, une liste des patients suivis)
            
            
        
    return render_template('doctor.html', doctor_data_dict=doctor_data_dict,patient_data=patient_data, new_patient=patients)


'''
@app.route('/doctor',methods=['GET', 'POST'])
def doctor():
    if 'role' not in session or session['role'] != 'doctor':
        return redirect(url_for('login'))  # Redirect to login if not logged in
    # Fetch doctor-specific data here, like doctor_id
    email = session.get('email')
    doctor_id = db.get_doctor_id_by_email(email)
    doctor_data = db.get_doctor_data(doctor_id)
    doctor_data_dict={
        'id':doctor_data[0],
        'first_name':doctor_data[1],
        'last_name':doctor_data[2],
        'email':doctor_data[3],
        'address':doctor_data[6],
        'phone_number':doctor_data[5]
        
    }
    # Fetch patients for the doctor
    patients = db.get_the_doctor_patients(doctor_id)
    
    # Handle POST request (adding a new patient)
    if request.method == 'POST':
        if 'add_patient' in request.form:
            patient_id = request.form.get('patient_id')
            
            # Add patient to the database
            db.doctor_Add_patient(doctor_id, patient_id)
            return redirect(url_for('doctor'))  # Refresh the page to show the updated list of patients

        if 'add_task' in request.form:
            patient_id = request.form.get('patient_id')
            task_type = request.form.get('task_type')  # 'caregiver' or 'patient'
            task = request.form.get('task')
            
            # Add task to the patient
            db.add_task_to_caregi(patient_id, task_type, task)
            return redirect(url_for('doctor'))  # Refresh the page to show the updated tasks

    
    return render_template('doctor.html',doctor_data_dict=doctor_data_dict)
'''

@app.route('/caregiver',methods=['GET', 'POST'])
def caregiver():
    if 'role' not in session or session['role'] != 'caregiver':
        return redirect(url_for('login'))  # Redirect to login if not logged in
    # Fetch doctor-specific data here, like doctor_id
    email = session.get('email')
    caregiver_id = db.get_caregiver_id_by_email(email)
    caregiver_data = db.get_caregiver_data(caregiver_id)
    caregiver_data_dict={
        'id':caregiver_data[0],
        'first_name':caregiver_data[1],
        'last_name':caregiver_data[2],
        'email':caregiver_data[3],
        'address':caregiver_data[6],
        'phone_number':caregiver_data[5]
        
    }
    
    return render_template('caregiver.html',caregiver_data_dict=caregiver_data_dict)

@app.route('/patient',methods=['GET', 'POST'])
def patient():
    if 'role' not in session or session['role'] != 'patient':
        return redirect(url_for('login'))  # Redirect to login if not logged in
    # Fetch doctor-specific data here, like doctor_id
    email = session.get('email')
    patient_id = db.get_patient_id_by_email(email)
    patient_data = db.get_patient_data(patient_id)
    
    patient_data_dict={
        'id':patient_data[0],
        'first_name':patient_data[1],
        'last_name':patient_data[2],
        'email':patient_data[3],
        'address':patient_data[6],
        'phone_number':patient_data[5]
        
    }
    
    return render_template('patient.html',patient_data_dict=patient_data_dict)

@app.route('/')
@app.route('/index')
def dashboard():
    return render_template('index.html')  # Ensure the correct template is rendered


if __name__ == '__main__':
    app.run(debug=True)
