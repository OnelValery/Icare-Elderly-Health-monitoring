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
            address TEXT
            
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
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            address TEXT
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

def create_patient_tasks():
    db.raw_query("""
    CREATE TABLE IF NOT EXISTS icare.patient_tasks (
        patient_task_id SERIAL PRIMARY KEY,
        task_description TEXT NOT NULL,
        scheduled_date TIMESTAMP NOT NULL,
        status VARCHAR(20) DEFAULT 'Pending',
        assigned_by VARCHAR(7) NOT NULL,
        assigned_for character varying(25) NOT NULL,
        CONSTRAINT fk_doctor FOREIGN KEY (assigned_by)
            REFERENCES doctors(doctor_id) ON UPDATE CASCADE ON DELETE CASCADE
        
    );
    """)
    db.commit()
    

def create_caregiver_tasks():
    db.raw_query("""
    CREATE TABLE IF NOT EXISTS icare.caregiver_tasks (
        caregiver_task_id SERIAL PRIMARY KEY,
        task_description TEXT NOT NULL,
        scheduled_date TIMESTAMP NOT NULL,
        status VARCHAR(20) DEFAULT 'Pending',
        assigned_by VARCHAR(7) NOT NULL,
        caregiver_id VARCHAR(7) NOT NULL,
        patient_id character varying(25) NOT NULL,
        CONSTRAINT fk_doctor FOREIGN KEY (assigned_by)
            REFERENCES doctors(doctor_id) ON UPDATE CASCADE ON DELETE CASCADE,
        CONSTRAINT fk_caregiver FOREIGN KEY (caregiver_id)
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
                REFERENCES caregiver_tasks(caregiver_task_id) ON UPDATE CASCADE ON DELETE CASCADE,
            CONSTRAINT fk_doctor FOREIGN KEY (doctor_id)
                REFERENCES doctors(doctor_id) ON UPDATE CASCADE ON DELETE CASCADE
        );
    """)
    db.commit()
    


# Devices table
def create_devices():
    db.raw_query("""
        CREATE TABLE IF NOT EXISTS icare.devices (
            device_id VARCHAR(20) PRIMARY KEY,    -- Unique device ID
            battery_percentage FLOAT NOT NULL
        );
    """)
    db.commit()


# Patient-Device relationship table
def create_patient_device():
    db.raw_query("""
        CREATE TABLE IF NOT EXISTS icare.patient_device (
            patient_id VARCHAR(10) NOT NULL,
            device_id VARCHAR(20) NOT NULL UNIQUE,  -- One device per patient
            linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_patient FOREIGN KEY (patient_id)
                REFERENCES icare.patients(patient_id) ON DELETE CASCADE ON UPDATE CASCADE,
            CONSTRAINT fk_device FOREIGN KEY (device_id)
                REFERENCES icare.devices(device_id) ON DELETE CASCADE ON UPDATE CASCADE,
            PRIMARY KEY (patient_id, device_id)
        );
    """)
    db.commit()


# Step counting data
def create_step_counting():
    db.raw_query("""
        CREATE TABLE IF NOT EXISTS icare.step_counting (
            step_id SERIAL PRIMARY KEY,
            device_id VARCHAR(20) NOT NULL,
            time_seconds BIGINT NOT NULL,
            step_count INT NOT NULL,
            acceleration_mag FLOAT NOT NULL,
            CONSTRAINT fk_device FOREIGN KEY (device_id)
                REFERENCES icare.devices(device_id) ON DELETE CASCADE ON UPDATE CASCADE
        );
    """)
    db.commit()


# Gyroscope data
def create_gyroscope():
    db.raw_query("""
        CREATE TABLE IF NOT EXISTS icare.gyroscope (
            gyroscope_id SERIAL PRIMARY KEY,
            device_id VARCHAR(20) NOT NULL,
            time_seconds BIGINT NOT NULL,
            rotation_speed FLOAT NOT NULL,
            gyroscope_x FLOAT NOT NULL,
            gyroscope_y FLOAT NOT NULL,
            gyroscope_z FLOAT NOT NULL,
            CONSTRAINT fk_device FOREIGN KEY (device_id)
                REFERENCES icare.devices(device_id) ON DELETE CASCADE ON UPDATE CASCADE
        );
    """)
    db.commit()


# Accelerometer data
def create_accelerometer():
    db.raw_query("""
        CREATE TABLE IF NOT EXISTS icare.accelerometer (
            accelerometer_id SERIAL PRIMARY KEY,
            device_id VARCHAR(20) NOT NULL,
            acceleration FLOAT NOT NULL,
            time_seconds BIGINT NOT NULL,
            accelerometer_x FLOAT NOT NULL,
            accelerometer_y FLOAT NOT NULL,
            accelerometer_z FLOAT NOT NULL,
            CONSTRAINT fk_device FOREIGN KEY (device_id)
                REFERENCES icare.devices(device_id) ON DELETE CASCADE ON UPDATE CASCADE
        );
    """)
    db.commit()


# Fall detection data
def create_fall_detection():
    db.raw_query("""
        CREATE TABLE IF NOT EXISTS icare.fall_detection (
            fall_detection_id SERIAL PRIMARY KEY,
            device_id VARCHAR(20) NOT NULL,
            fall_detected BOOLEAN NOT NULL,
            time_of_fall BIGINT NOT NULL,  -- In UNIX timestamp (milliseconds),
            CONSTRAINT fk_device FOREIGN KEY (device_id)
                REFERENCES icare.devices(device_id) ON DELETE CASCADE ON UPDATE CASCADE
        );
    """)
    db.commit()


# Heart rate data
def create_heart_rate():
    db.raw_query("""
        CREATE TABLE IF NOT EXISTS icare.heart_rate (
            heart_rate_id SERIAL PRIMARY KEY,
            device_id VARCHAR(20) NOT NULL,
            bpm INT NOT NULL,
            beat_average FLOAT NOT NULL,
            time_seconds BIGINT NOT NULL,
            heart_rate_value BIGINT NOT NULL,
            CONSTRAINT fk_device FOREIGN KEY (device_id)
                REFERENCES icare.devices(device_id) ON DELETE CASCADE ON UPDATE CASCADE
        );
    """)
    db.commit()


# SpO2 data
def create_spo2():
    db.raw_query("""
        CREATE TABLE IF NOT EXISTS icare.spo2 (
            spo2_id SERIAL PRIMARY KEY,
            device_id VARCHAR(20) NOT NULL,
            time_seconds BIGINT NOT NULL,
            spo2_percent INT NOT NULL,
            CONSTRAINT fk_device FOREIGN KEY (device_id)
                REFERENCES icare.devices(device_id) ON DELETE CASCADE ON UPDATE CASCADE
        );
    """)
    db.commit()


# Temperature data
def create_temperature():
    db.raw_query("""
        CREATE TABLE IF NOT EXISTS icare.temperature (
            temperature_id SERIAL PRIMARY KEY,
            device_id VARCHAR(20) NOT NULL,
            temperature FLOAT NOT NULL,
            time_seconds BIGINT NOT NULL,
            CONSTRAINT fk_device FOREIGN KEY (device_id)
                REFERENCES icare.devices(device_id) ON DELETE CASCADE ON UPDATE CASCADE
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
    


def mark_patient_task_completed(task_id, is_for_patient=True):
    """ Mark a task as completed """
   
    db.raw_query("""
        UPDATE icare.patient_tasks
        SET status = 'Completed'
        WHERE patient_task_id = %s;
    """, (task_id,))

    db.commit()
    
def mark_caregiver_task_completed(task_id, is_for_patient=True):
    """ Mark a task as completed """
   
    db.raw_query("""
        UPDATE icare.caregiver_tasks
        SET status = "Completed"
        WHERE caregiver_task_id = %s;
    """, (task_id,))

    db.commit()
    
def insert_patient_task(task_id, description, scheduled_date, status, assigned_by, assigned_to):
    """
    Insert a new task assigned by a doctor to a patient 
    """
    db.raw_query("""
        INSERT INTO icare.patient_tasks(patient_task_id, task_description, scheduled_date, status, assigned_by,patient_id)
        VALUES (%s, %s, %s, %s,%s,%s);
    """, (task_id, description, scheduled_date, status, assigned_by, assigned_to))
    
    db.commit()
    
def insert_caregiver_task(task_id, description, scheduled_date, status, assigned_by, assigned_to,assigned_for,patient_id):
    """
    Insert a new task assigned by a doctor to a  caregiver.
    """
    db.raw_query("""
        INSERT INTO icare.caregiver_tasks(caregiver_task_id, task_description, scheduled_date, status, assigned_by, caregiver_id,patient_id)
        VALUES (%s, %s, %s, %s,%s,%s,%s);
    """, (task_id, description, scheduled_date, status, assigned_by, assigned_to,assigned_for,patient_id))
    
    db.commit()
    
def assign_caregiver_to_patient(patient_id, caregiver_id):
    """ Assign a caregiver to a patient """
    db.raw_query("""
        UPDATE icare.patients_caregivers
        SET caregiver_id = %s
        WHERE patient_id = %s;
    """, (caregiver_id, patient_id))
    
    db.commit()
    
def insert_doctor(doctor_id,firstname, lastname, phone_number, email, password, address):
    """ Insert a new doctor into the doctors table """
     # Generate a unique 7-digit ID
    doctor_id 
    db.raw_query("""
        INSERT INTO icare.doctors (doctor_id, first_name, last_name, email, password, address)
        VALUES (%s, %s, %s, %s, %s,%s)
        RETURNING doctor_id;
    """, (doctor_id, firstname, lastname, email, password, address))


    # Insert phone number separately (if provided)
    if phone_number:
        db.raw_query("""
            INSERT INTO icare.doctor_phone_numbers (doctor_id, phone_number)
            VALUES (%s, %s);
        """, (doctor_id, phone_number))

    db.commit()
    print(f"Doctor {firstname} {lastname} inserted with ID: {doctor_id}")
    return doctor_id

    
def insert_patient(patient_id,firstname, lastname, phone_number, email, password, address, doctor_id=None):
    """ Insert a new patient into the patients table """
    # Generate a unique 10-digit ID for the patient
     
    db.raw_query("""
        INSERT INTO icare.patients (patient_id,first_name, last_name, email, password, address, doctor_id)
        VALUES (%s,%s, %s, %s, %s, %s, %s)
        RETURNING patient_id;
    """, (patient_id,firstname, lastname, email, password, address, doctor_id))


    # Insert phone number separately
    if phone_number:
        db.raw_query("""
            INSERT INTO icare.patient_phone_numbers (patient_id, phone_number)
            VALUES (%s, %s);
        """, (patient_id, phone_number))

    db.commit()
    print(f"Patient {firstname} {lastname} inserted with ID: {patient_id}")
    return patient_id

    
def insert_caregiver(caregiver_id,firstname, lastname, phone_number, email, password, address):
    """ Insert a new caregiver into the caregivers table """
    # Generate a unique 7-digit ID
    caregiver_id 
    db.raw_query("""
        INSERT INTO icare.caregivers (caregiver_id,first_name, last_name, email, password, address)
        VALUES (%s, %s, %s, %s, %s,%s)
        RETURNING caregiver_id;
    """, (caregiver_id, firstname, lastname, email, password, address))


    # Insert phone number separately
    if phone_number:
        db.raw_query("""
            INSERT INTO icare.caregiver_phone_numbers (caregiver_id, phone_number)
            VALUES (%s, %s);
        """, (caregiver_id, phone_number))

    db.commit()
    print(f"Caregiver {firstname} {lastname} inserted with ID: {caregiver_id}")
    return caregiver_id

def insert_device(device_id, battery_percentage):
    """Insert a new device record."""
    try:
        db.raw_query("""
            INSERT INTO icare.devices (device_id, battery_percentage)
            VALUES (%s, %s)
            ON CONFLICT (device_id) DO UPDATE 
            SET battery_percentage = EXCLUDED.battery_percentage;
        """, (device_id, battery_percentage))
        db.commit()
    except Exception as e:
        print(f"Error inserting device: {e}")
        
def insert_step_counting(step_id,device_id, time, step_count, acceleration_mag):
    """Insert step counting data."""
    try:
        db.raw_query("""
            INSERT INTO icare.step_counting (step_id,device_id, time_seconds, step_count, acceleration_mag)
            VALUES (%s,%s,%s, %s, %s);
        """, (step_id, device_id, time, step_count, acceleration_mag))
        db.commit()
    except Exception as e:
        print(f"Error inserting step counting data: {e}")
        
def insert_gyroscope(gyroscope_id,device_id, time, rotation_speed, gyroscope_x, gyroscope_y, gyroscope_z):
    """Insert gyroscope data."""
    try:
        db.raw_query("""
            INSERT INTO icare.gyroscope (gyroscope_id,device_id, time_seconds, rotation_speed, gyroscope_x, gyroscope_y, gyroscope_z)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """, (gyroscope_id, device_id, time, rotation_speed, gyroscope_x, gyroscope_y, gyroscope_z))
        db.commit()
    except Exception as e:
        print(f"Error inserting gyroscope data: {e}")
        
def insert_accelerometer(accelerometer_id,device_id, acceleration, time, accelerometer_x, accelerometer_y, accelerometer_z):
    """Insert accelerometer data."""
    try:
        db.raw_query("""
            INSERT INTO icare.accelerometer (accelerometer_id, device_id, acceleration, time_seconds, accelerometer_x, accelerometer_y, accelerometer_z)
            VALUES (%s,%s, %s, %s, %s, %s, %s);
        """, (accelerometer_id,device_id, acceleration, time, accelerometer_x, accelerometer_y, accelerometer_z))
        db.commit()
    except Exception as e:
        print(f"Error inserting accelerometer data: {e}")
        
        
def insert_fall_detection(fall_detection_id,device_id, fall_detected, time_of_fall):
    """Insert fall detection data."""
    try:
        db.raw_query("""
            INSERT INTO icare.fall_detection (fall_detection_id, device_id, fall_detected, time_of_fall)
            VALUES (%s, %s, %s, %s);
        """, (fall_detection_id, device_id, fall_detected, time_of_fall))
        db.commit()
    except Exception as e:
        print(f"Error inserting fall detection data: {e}")
        
        
def insert_heart_rate(heart_rate_id, device_id, bpm, beat_average, time, heart_rate_value):
    """Insert heart rate data."""
    try:
        db.raw_query("""
            INSERT INTO icare.heart_rate (heart_rate_id,device_id, bpm, beat_average, time_seconds, heart_rate_value)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (heart_rate_id,device_id, bpm, beat_average, time, heart_rate_value))
        db.commit()
    except Exception as e:
        print(f"Error inserting heart rate data: {e}")
        
        
def insert_spo2(spo2_id,device_id, time, spo2_percent):
    """Insert SpO2 data."""
    try:
        db.raw_query("""
            INSERT INTO icare.spo2 (spo2_id,device_id, time_seconds, spo2_percent)
            VALUES (%s, %s, %s, %s);
        """, (spo2_id,device_id, time, spo2_percent))
        db.commit()
    except Exception as e:
        print(f"Error inserting SpO2 data: {e}")
        
def insert_temperature(temperature_id,device_id, temperature, time):
    """Insert temperature data."""
    try:
        db.raw_query("""
            INSERT INTO icare.temperature (temperature_id,device_id, temperature, time_seconds)
            VALUES (%s, %s, %s, %s);
        """, (temperature_id,device_id, temperature, time))
        db.commit()
    except Exception as e:
        print(f"Error inserting temperature data: {e}")


def reset():
    db.raw_query("""
        DROP TABLE IF EXISTS icare.doctors,
        icare.patients,
        icare.caregivers,
        icare.patients_caregivers,
        icare.patient_tasks,
        icare.caregiver_tasks,
        icare.task_followups,
        icare.doctor_phone_numbers,
        icare.patient_phone_numbers,
        icare.caregiver_phone_numbers,
        icare.heart_rate,
        icare.gyroscope,
        icare.accelerometer,
        icare.spo2,
        icare.step_counting,
        icare.temperature,
        icare.fall_detection,
        icare.patient_device,
        icare.devices CASCADE;
        
    """)
    db.commit()


  
def create_all_tables():
    create_doctors()
    create_patients()
    create_caregivers()
    create_patients_caregivers()
    create_patient_tasks()
    create_caregiver_tasks()
    create_task_followups()
    create_patient_phone_numbers()
    create_caregiver_phone_numbers()
    create_doctor_phone_numbers()
    create_devices()
    create_patient_device()
    create_step_counting()
    create_gyroscope()
    create_accelerometer()
    create_fall_detection()
    create_heart_rate()
    create_spo2()
    create_temperature()


 
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
    '''
    insert_caregiver_task(
    task_id=1,
    description="Check blood pressure",
    scheduled_date="2025-04-01 14:00:00",
    status="Pending",
    assigned_by=1234567,    # Doctor ID
    assigned_to=1234568,  # Patient ID
    assigned_type="patient"
)
'''



  
    

   











