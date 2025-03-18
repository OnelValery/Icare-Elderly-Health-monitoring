import random
from faker import Faker
#from random_username.generate import generate_completname
from db import db
import datetime
import requests
import urllib.request
import aiohttp
import asyncio
import secrets
import time
import traceback
import sys
import glob
import os

fake = Faker()


def create_doctors():
    db.raw_query("""
        CREATE TABLE IF NOT EXISTS icare.doctors (
            doctor_id VARCHAR(7) PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    db.commit()

def create_doctor_phone_numbers():
    """ Create the table for storing doctor phone numbers """
    
    db.raw_query("""
    CREATE TABLE IF NOT EXISTS icare.doctor_phone_numbers (
        doctor_id VARCHAR(7) NOT NULL,  -- Ensure this matches the doctor_id type in the doctors table
        phone_number VARCHAR(25) NOT NULL,
        CONSTRAINT doctor_phone_numbers_pkey PRIMARY KEY (doctor_id, phone_number),
        CONSTRAINT doctor_phone_numbers_fkey FOREIGN KEY (doctor_id)
            REFERENCES icare.doctors (doctor_id) ON UPDATE CASCADE ON DELETE CASCADE
            
    );
     """)
    db.commit()




def create_patients():
    db.raw_query("""
        CREATE TABLE IF NOT EXISTS icare.patients (
            patient_id character varying(25) PRIMARY KEY,  -- Ensure this is the primary key
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            address TEXT,
            doctor_id VARCHAR(7) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_doctor FOREIGN KEY (doctor_id)
                REFERENCES icare.doctors(doctor_id) ON UPDATE CASCADE ON DELETE CASCADE
        );
    """)
    db.commit()


    
def create_patient_phone_numbers():
    """ Create the table for storing patient phone numbers """
    db.raw_query("""
    CREATE TABLE IF NOT EXISTS icare.patient_phone_numbers (
        patient_id character varying(25) COLLATE pg_catalog."default" NOT NULL,
        phone_number character varying(25) COLLATE pg_catalog."default" NOT NULL,
        CONSTRAINT patient_phone_numbers_pkey PRIMARY KEY (patient_id, phone_number),
        CONSTRAINT patient_phone_numbers_fkey FOREIGN KEY (patient_id)
            REFERENCES icare.patients (patient_id) MATCH SIMPLE
            ON UPDATE CASCADE
            ON DELETE CASCADE
    );
    """)
    db.commit()


def create_caregivers():
    db.raw_query("""
        CREATE TABLE IF NOT EXISTS icare.caregivers (
            caregiver_id VARCHAR(25) PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            phone_number VARCHAR(20),
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    db.commit()

def create_caregiver_phone_numbers():
    """ Create the table for storing caregiver phone numbers """
    db.raw_query("""
    CREATE TABLE IF NOT EXISTS icare.caregiver_phone_numbers (
        caregiver_id character varying(25) COLLATE pg_catalog."default" NOT NULL,
        phone_number VARCHAR(25) NOT NULL,
        CONSTRAINT caregiver_phone_numbers_pkey PRIMARY KEY (caregiver_id, phone_number),
        CONSTRAINT caregiver_phone_numbers_fkey FOREIGN KEY (caregiver_id)
            REFERENCES caregivers (caregiver_id) MATCH SIMPLE
            ON UPDATE CASCADE
            ON DELETE CASCADE
    );
    """)
    db.commit()

def create_patients_caregivers():
    # Set the search path to the 'icare' schema
    db.raw_query("SET search_path TO icare;")
    
    db.raw_query("""
        CREATE TABLE IF NOT EXISTS icare.patients_caregivers (
            patient_id character varying(25) COLLATE pg_catalog."default" NOT NULL,
            caregiver_id VARCHAR(25) NOT NULL,
            CONSTRAINT pk_patients_caregivers PRIMARY KEY (patient_id, caregiver_id),
            CONSTRAINT fk_patient FOREIGN KEY (patient_id)
                REFERENCES icare.patients(patient_id) ON UPDATE CASCADE ON DELETE CASCADE,
            CONSTRAINT fk_caregiver FOREIGN KEY (caregiver_id)
                REFERENCES icare.caregivers(caregiver_id) ON UPDATE CASCADE ON DELETE CASCADE
        );
    """)
    db.commit()

def create_tasks():
    db.raw_query("""
        CREATE TABLE IF NOT EXISTS icare.tasks (
            task_id SERIAL PRIMARY KEY,
            task_description TEXT NOT NULL,
            scheduled_date TIMESTAMP NOT NULL,
            status VARCHAR(20) DEFAULT 'Pending',  -- e.g., Pending, Completed
            assigned_by VARCHAR(7) NOT NULL,  -- doctor_id who assigns the task
            assigned_to character varying(25) ,  -- patient_id or caregiver_id
            task_type VARCHAR(50),  -- 'patient' or 'caregiver' to know who is assigned
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_doctor FOREIGN KEY (assigned_by)
                REFERENCES doctors(doctor_id) ON UPDATE CASCADE ON DELETE CASCADE,
            CONSTRAINT fk_patient FOREIGN KEY (assigned_to)
                REFERENCES patients(patient_id) ON UPDATE CASCADE ON DELETE CASCADE,
            CONSTRAINT fk_caregiver FOREIGN KEY (assigned_to)
                REFERENCES caregivers(caregiver_id) ON UPDATE CASCADE ON DELETE CASCADE
        );
    """)
    db.commit()

def create_task_followups():
    db.raw_query("""
        CREATE TABLE IF NOT EXISTS icare.task_followups (
            followup_id SERIAL PRIMARY KEY,
            task_id INTEGER NOT NULL,
            doctor_id VARCHAR(7) NOT NULL,
            message TEXT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_task FOREIGN KEY (task_id)
                REFERENCES tasks(task_id) ON UPDATE CASCADE ON DELETE CASCADE,
            CONSTRAINT fk_doctor FOREIGN KEY (doctor_id)
                REFERENCES doctors(doctor_id) ON UPDATE CASCADE ON DELETE CASCADE
        );
    """)
    db.commit()
    
def create_patient_data():
    db.raw_query("""
        CREATE TABLE IF NOT EXISTS icare.patient_data (
            data_id SERIAL PRIMARY KEY,            -- Unique ID for each record
            patient_id character varying(25) COLLATE pg_catalog."default" NOT NULL,           -- Foreign key to patients
            device_id VARCHAR(50) NOT NULL,        -- ESP32 identifier in case multiple devices per patient
            heart_rate INTEGER,                    -- Heart rate in BPM
            temperature DECIMAL(5,2),              -- Temperature in °C or °F
            blood_pressure_systolic INTEGER,       -- Systolic blood pressure
            blood_pressure_diastolic INTEGER,      -- Diastolic blood pressure
            spO2 DECIMAL(5,2),                     -- Oxygen saturation
            ecg_signal BYTEA,                      -- ECG data (binary blob for signal)
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Exact time of measurement
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Time of insertion
            CONSTRAINT fk_patient FOREIGN KEY (patient_id)
                REFERENCES patients(patient_id) ON DELETE CASCADE
        );
    """)
    db.commit()


 

def insert_caregiver_phone_number(caregiver_id, phone_number):
    """ Insert a phone number for a caregiver """
    db.raw_query("""
        INSERT INTO icare.caregiver_phone_numbers (caregiver_id, phone_number)
        VALUES (%s, %s);
    """, (caregiver_id, phone_number))
    
    db.commit()

def insert_patient_phone_number(patient_id, phone_number):
    """ Insert a phone number for a patient """
    db.raw_query("""
        INSERT INTO icare.patient_phone_numbers (patient_id, phone_number)
        VALUES (%s, %s);
    """, (patient_id, phone_number))
    
    db.commit()
    
def insert_doctor_phone_number(doctor_id, phone_number):
    """ Insert a phone number for a doctor """
    db.raw_query("""
        INSERT INTO icare.doctor_phone_numbers (doctor_id, phone_number)
        VALUES (%s, %s);
    """, (doctor_id, phone_number))
    
    db.commit()
    
def insert_patient_data(patient_id, device_id, heart_rate, temperature, bp_systolic, bp_diastolic, spO2, ecg_signal, timestamp):
    """
    Insert time-series patient data from ESP32
    """
    db.raw_query("""
        INSERT INTO icare.patient_data (
            patient_id, device_id, heart_rate, temperature, 
            blood_pressure_systolic, blood_pressure_diastolic, 
            spO2, ecg_signal, timestamp
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """, (
        patient_id, device_id, heart_rate, temperature,
        bp_systolic, bp_diastolic, spO2, ecg_signal, timestamp
    ))

    db.commit()

def mark_task_completed(task_id, is_for_patient=True):
    """ Mark a task as completed """
    if is_for_patient:
        db.raw_query("""
            UPDATE icare.task_for_patient
            SET completed = TRUE
            WHERE task_id = %s;
        """, (task_id,))
    else:
        db.raw_query("""
            UPDATE icare.task_for_caregivers
            SET completed = TRUE
            WHERE task_id = %s;
        """, (task_id,))

    db.commit()
    
def insert_task(doctor_id, assigned_to, assigned_type, description, scheduled_for):
    """
    Insert a new task assigned by a doctor to a patient or caregiver.
    
    assigned_type: 'patient' or 'caregiver'
    """
    if assigned_type == 'patient':
        db.raw_query("""
            INSERT INTO task_for_patient (doctor_id, patient_id, description, scheduled_for)
            VALUES (%s, %s, %s, %s);
        """, (doctor_id, assigned_to, description, scheduled_for))

    elif assigned_type == 'caregiver':
        db.raw_query("""
            INSERT INTO task_for_caregivers (doctor_id, caregiver_id, description, scheduled_for)
            VALUES (%s, %s, %s, %s);
        """, (doctor_id, assigned_to, description, scheduled_for))
    
    db.commit()
    
def assign_caregiver_to_patient(patient_id, caregiver_id):
    """ Assign a caregiver to a patient """
    db.raw_query("""
        UPDATE patients
        SET caregiver_id = %s
        WHERE patient_id = %s;
    """, (caregiver_id, patient_id))
    
    db.commit()
    
def insert_doctor(firstname, lastname, phone_number, email, password, address):
    """ Insert a new doctor into the doctors table """
     # Generate a unique 7-digit ID
    doctor_id = str(random.randint(1000000, 9999999))
    db.raw_query("""
        INSERT INTO doctors (doctor_id, firstname, lastname, email, password, address)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING doctor_id;
    """, (doctor_id, firstname, lastname, email, password, address))


    # Insert phone number separately (if provided)
    if phone_number:
        db.raw_query("""
            INSERT INTO doctor_phone_numbers (doctor_id, phone_number)
            VALUES (%s, %s);
        """, (doctor_id, phone_number))

    db.commit()
    print(f"Doctor {firstname} {lastname} inserted with ID: {doctor_id}")
    return doctor_id

    
def insert_patient(firstname, lastname, phone_number, email, password, address, doctor_id=None, caregiver_id=None):
    """ Insert a new patient into the patients table """
    # Generate a unique 10-digit ID for the patient
    patient_id = str(random.randint(1000000000, 9999999999))
    db.raw_query("""
        INSERT INTO patients (patient_id,firstname, lastname, email, password, address, doctor_id, caregiver_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING patient_id;
    """, (patient_id,firstname, lastname, email, password, address, doctor_id, caregiver_id))


    # Insert phone number separately
    if phone_number:
        db.raw_query("""
            INSERT INTO patient_phone_numbers (patient_id, phone_number)
            VALUES (%s, %s);
        """, (patient_id, phone_number))

    db.commit()
    print(f"Patient {firstname} {lastname} inserted with ID: {patient_id}")
    return patient_id

    
def insert_caregiver(firstname, lastname, phone_number, email, password, address):
    """ Insert a new caregiver into the caregivers table """
    # Generate a unique 7-digit ID
    caregiver_id = str(random.randint(1000000, 9999999))
    db.raw_query("""
        INSERT INTO caregivers (caregiver_id,firstname, lastname, email, password, address)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING caregiver_id;
    """, (caregiver_id, firstname, lastname, email, password, address))


    # Insert phone number separately
    if phone_number:
        db.raw_query("""
            INSERT INTO caregiver_phone_numbers (caregiver_id, phone_number)
            VALUES (%s, %s);
        """, (caregiver_id, phone_number))

    db.commit()
    print(f"Caregiver {firstname} {lastname} inserted with ID: {caregiver_id}")
    return caregiver_id

def reset():
  db.raw_query("""
  drop table  doctors, create_patients ,create_caregivers, create_patients_caregivers, create_tasks,create_task_followups,create_doctor_phone_numbers,create_patient_phone_numbers,create_caregiver_phone_numbers CASCADE
  """)
  db.commit()
  
def create_all_tables():
    create_doctors()
    create_patients()
    create_caregivers()
    create_patients_caregivers()
    create_tasks()
    create_task_followups()
    
    create_patient_phone_numbers()
    create_caregiver_phone_numbers()
    create_doctor_phone_numbers()







 
def main(): 
    try: 
      generation_size = sys.argv[1].lower()
      if generation_size == 'reset':
        reset()
        print("Reset successful, ready for data to be generated.")
        db.close()
        db.new_connection()
      elif generation_size == 'generate':
        print("Creating tables...")
        create_all_tables()
        print("Tables creation completed successfully! ")
      
    except Exception as e:
      print(e)
      db.close()
      db.new_connection()

if __name__ == "__main__":
  main()
  print("Creating tables...")
  create_all_tables()
  print("Tables creation completed successfully! ")
 
  

  