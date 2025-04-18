import sys
from dbconnection import new_connection
import os
import secrets
import datetime

# Change these credentials to change db
dbname = "health_monitor"
user = "postgres"
password = "HealthMonitorPass123"
host = "localhost"
port = "5432"
schema = "icare"

class DB:
    def __init__(self, dbname, user, password, host, port, schema):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.schema = schema

    def new_connection(self):
        self.connection = new_connection(self.dbname, self.user, self.password, self.host, self.port, self.schema)
        self.cursor = self.connection.cursor

    def close(self):
        self.connection.close()

    def commit(self):
        self.connection.commit()

    def raw_query(self, query, params=None):
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)

    # ------------------------------
    # Helper Methods
    # ------------------------------
    def fetch_all(self):
        return self.cursor.fetchall()

    def fetch_one(self):
        return self.cursor.fetchone()

    # ---------------------------------------------------------
    # Validation Methods
    # ---------------------------------------------------------
    def valid_doctor_account(self, email, password):
        self.raw_query("""
            SELECT email, password FROM icare.doctors
            WHERE email = %s AND password = %s;
        """, (email, password))
        return self.fetch_one() is not None

    def valid_patient_account(self, email, password):
        self.raw_query("""
            SELECT email, password FROM icare.patients
            WHERE email = %s AND password = %s;
        """, (email, password))
        return self.fetch_one() is not None

    def valid_caregiver_account(self, email, password):
        self.raw_query("""
            SELECT email, password FROM icare.caregivers
            WHERE email = %s AND password = %s;
        """, (email, password))
        return self.fetch_one() is not None

    # ---------------------------------------------------------
    # Registration Methods
    # ---------------------------------------------------------
    def register_doctor(self, doctor_id, first_name, last_name, phone_number, email, password, address):
        try:
            self.raw_query("""
                INSERT INTO icare.doctors (doctor_id, first_name, last_name, email, password, phone_number, address) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (doctor_id, first_name, last_name, email, password, phone_number, address))
            self.commit()
            return True
        except Exception as e:
            print(f"Error adding doctor: {e}")
            return False

    def register_caregiver(self, caregiver_id, first_name, last_name, phone_number, email, password, address):
        try:
            self.raw_query("""
                INSERT INTO icare.caregivers (caregiver_id, first_name, last_name, email, password, phone_number, address) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (caregiver_id, first_name, last_name, email, password, phone_number, address))
            self.commit()
            return True
        except Exception as e:
            print(f"Error adding caregiver: {e}")
            return False

    def register_patient(self, patient_id, first_name, last_name, phone_number, email, password, address):
        try:
            self.raw_query("""
                INSERT INTO icare.patients (patient_id, first_name, last_name, email, password, phone_number, address, doctor_id, caregiver_id) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (patient_id, first_name, last_name, email, password, phone_number, address, None, None))
            self.commit()
            return True
        except Exception as e:
            print(f"Error adding patient: {e}")
            return False

    # ---------------------------------------------------------
    # "Get by email" Methods
    # ---------------------------------------------------------
    def get_doctor_id_by_email(self, email):
        self.raw_query("""
            SELECT doctor_id FROM icare.doctors WHERE email = %s;
        """, (email,))
        result = self.fetch_one()
        return result[0] if result else None

    def get_patient_id_by_email(self, email):
        self.raw_query("""
            SELECT patient_id FROM icare.patients WHERE email = %s;
        """, (email,))
        result = self.fetch_one()
        return result[0] if result else None

    def get_caregiver_id_by_email(self, email):
        self.raw_query("""
            SELECT caregiver_id FROM icare.caregivers WHERE email = %s;
        """, (email,))
        result = self.fetch_one()
        return result[0] if result else None

    # ---------------------------------------------------------
    # Retrieve Full Row Data
    # ---------------------------------------------------------
    def get_doctor_data(self, doctor_id):
        self.raw_query("SELECT * FROM icare.doctors WHERE doctor_id = %s;", (doctor_id,))
        return self.fetch_one()

    def get_patient_data(self, patient_id):
        self.raw_query("SELECT * FROM icare.patients WHERE patient_id = %s;", (patient_id,))
        return self.fetch_one()

    def get_caregiver_data(self, caregiver_id):
        self.raw_query("SELECT * FROM icare.caregivers WHERE caregiver_id = %s;", (caregiver_id,))
        return self.fetch_one()

    def get_patient_by_id(self, patient_id):
        try:
            self.raw_query("SELECT * FROM icare.patients WHERE patient_id = %s", (patient_id,))
            return self.fetch_one()
        except Exception as e:
            print(f"Error fetching patient by ID: {e}")
            return None

    def get_patient_name(self, patient_id):
        try:
            self.raw_query("SELECT first_name, last_name FROM icare.patients WHERE patient_id = %s", (patient_id,))
            return self.fetch_one()
        except Exception as e:
            print(f"Error fetching patient name: {e}")
            return None
        
    def get_the_doctor_patients(self, doctor_id):
        try:
            self.raw_query("""
                SELECT patient_id, first_name, last_name, email, phone_number, address, caregiver_id
                FROM icare.patients
                WHERE doctor_id = %s
            """, (doctor_id,))
            rows = self.fetch_all()
            # Each row is like: (patient_id, first_name, last_name, email, phone_number, address, caregiver_id)
            patients = []
            for r in rows:
                patients.append({
                    "patient_id": r[0],
                    "first_name": r[1],
                    "last_name":  r[2],
                    "patient_email": r[3],
                    "phone_number":  r[4],
                    "patient_adress": r[5],  
                    "caregiver_id":   r[6]
                })
            return patients
        except Exception as e:
            print(f"Error in get_the_doctor_patients: {e}")
            return []

    # ---------------------------------------------------------
    # Update and Delete Methods
    # ---------------------------------------------------------
    def remove_doctor_for_patient(self, doctor_id, patient_id):
        try:
            self.raw_query("SELECT doctor_id FROM icare.patients WHERE patient_id = %s", (patient_id,))
            patient = self.fetch_one()
            if patient:
                current_doctor_id = patient[0]
                if current_doctor_id == doctor_id:
                    self.raw_query("UPDATE icare.patients SET doctor_id = %s WHERE patient_id = %s", (None, patient_id))
                    self.commit()
                    return True
                else:
                    return False
            else:
                return False
        except Exception as e:
            print(f"Error removing doctor for patient: {e}")
            return None

    def doctor_add_patient(self, doctor_id, patient_id):
        try:
            self.raw_query("SELECT patient_id FROM icare.patients WHERE patient_id = %s", (patient_id,))
            result = self.fetch_all()
            if result:
                if doctor_id is None:
                    print("Error: Invalid doctor_id")
                    return False
                self.raw_query("UPDATE icare.patients SET doctor_id = %s WHERE patient_id = %s AND doctor_id IS NULL", (doctor_id, patient_id))
                self.commit()
                self.raw_query("SELECT doctor_id FROM icare.patients WHERE patient_id = %s", (patient_id,))
                updated_doctor_id = self.fetch_one()
                if updated_doctor_id and updated_doctor_id[0] == doctor_id:
                    return True
                else:
                    print("Error: Failed to update doctor_id.")
                    return False
            else:
                return False
        except Exception as e:
            print(f"Error adding patient to doctor: {e}")
            return None

    def delete_caregiver(self, caregiver_id):
        self.raw_query("DELETE FROM icare.caregivers WHERE caregiver_id = %s", (caregiver_id,))
        self.commit()

    def delete_doctor(self, doctor_id):
        self.raw_query("DELETE FROM icare.doctors WHERE doctor_id = %s", (doctor_id,))
        self.commit()

    def delete_patient(self, patient_id):
        self.raw_query("DELETE FROM icare.patients WHERE patient_id = %s", (patient_id,))
        self.commit()

    def update_caregivers(self, caregiver_id, update_part, upvalue):
        sql = f"UPDATE icare.caregivers SET {update_part} = %s WHERE caregiver_id = %s"
        self.raw_query(sql, (upvalue, caregiver_id))
        self.commit()

    def update_doctors(self, doctor_id, update_part, upvalue):
        sql = f"UPDATE icare.doctors SET {update_part} = %s WHERE doctor_id = %s"
        self.raw_query(sql, (upvalue, doctor_id))
        self.commit()

    def update_patients(self, patient_id, update_part, upvalue):
        sql = f"UPDATE icare.patients SET {update_part} = %s WHERE patient_id = %s"
        self.raw_query(sql, (upvalue, patient_id))
        self.commit()

    def insert_phone_number_of_caregivers(self, caregiver_id, phone_number):
        self.raw_query("""
            INSERT INTO icare.caregivers_phone_numbers (caregiver_id, phone_number) 
            VALUES (%s, %s)
        """, (caregiver_id, phone_number))
        self.commit()

    def update_phone_number_of_caregivers(self, caregiver_id, phone_number):
        self.raw_query("""
            UPDATE icare.caregivers_phone_numbers 
            SET phone_number = %s WHERE caregiver_id = %s
        """, (phone_number, caregiver_id))
        self.commit()

    def insert_phone_number_of_patients(self, patient_id, phone_number):
        self.raw_query("""
            INSERT INTO icare.patients_phone_numbers (patient_id, phone_number) 
            VALUES (%s, %s)
        """, (patient_id, phone_number))
        self.commit()

    def update_phone_number_of_patients(self, patient_id, phone_number):
        self.raw_query("""
            UPDATE icare.patients_phone_numbers 
            SET phone_number = %s WHERE patient_id = %s
        """, (phone_number, patient_id))
        self.commit()

    def insert_phone_number_of_doctors(self, doctor_id, phone_number):
        self.raw_query("""
            INSERT INTO icare.doctors_phone_numbers (doctor_id, phone_number) 
            VALUES (%s, %s)
        """, (doctor_id, phone_number))
        self.commit()

    def update_phone_number_of_doctors(self, doctor_id, phone_number):
        self.raw_query("""
            UPDATE icare.doctors_phone_numbers 
            SET phone_number = %s WHERE doctor_id = %s
        """, (phone_number, doctor_id))
        self.commit()

    # ---------------------------------------------------------
    # Sensor Data Retrieval Methods
    # ---------------------------------------------------------
    def get_patient_heart_rate(self, patient_id):
        query = """
            SELECT timestamp, heart_rate FROM icare.heart_rate
            WHERE patient_id = %s ORDER BY timestamp DESC;
        """
        self.raw_query(query, (patient_id,))
        return self.fetch_all()

    def get_patient_spo2_levels(self, patient_id):
        query = """
            SELECT timestamp, spo2_level FROM icare.spo2
            WHERE patient_id = %s ORDER BY timestamp DESC;
        """
        self.raw_query(query, (patient_id,))
        return self.fetch_all()

    def get_patient_temperature(self, patient_id):
        query = """
            SELECT timestamp, temperature FROM icare.temperature
            WHERE patient_id = %s ORDER BY timestamp DESC;
        """
        self.raw_query(query, (patient_id,))
        return self.fetch_all()

    def get_patient_step_count(self, patient_id):
        query = """
            SELECT date, step_count FROM icare.step_counting
            WHERE patient_id = %s ORDER BY date DESC;
        """
        self.raw_query(query, (patient_id,))
        return self.fetch_all()

    def get_patient_fall_events(self, patient_id):
        query = """
            SELECT timestamp, event_details FROM icare.fall_detection
            WHERE patient_id = %s ORDER BY timestamp DESC;
        """
        self.raw_query(query, (patient_id,))
        return self.fetch_all()

    def get_patient_gyroscope_data(self, patient_id):
        query = """
            SELECT timestamp, x_axis, y_axis, z_axis FROM icare.gyroscope
            WHERE patient_id = %s ORDER BY timestamp DESC;
        """
        self.raw_query(query, (patient_id,))
        return self.fetch_all()

    def get_patient_accelerometer_data(self, patient_id):
        query = """
            SELECT timestamp, x_axis, y_axis, z_axis FROM icare.accelerometer
            WHERE patient_id = %s ORDER BY timestamp DESC;
        """
        self.raw_query(query, (patient_id,))
        return self.fetch_all()

    def get_patient_tasks(self, patient_id):
        query = """
            SELECT task_description, status FROM icare.patient_tasks
            WHERE assigned_for = %s ORDER BY scheduled_date DESC;
        """
        self.raw_query(query, (patient_id,))
        return self.fetch_all()

    def get_patient_tasks_info(self, patient_id):
        query = """
            SELECT * FROM icare.patient_tasks
            WHERE assigned_for = %s ORDER BY scheduled_date DESC;
        """
        self.raw_query(query, (patient_id,))
        return self.fetch_all()

    def get_caregiver_tasks_info(self, caregiver_id, patient_id):
        query = """
            SELECT * FROM icare.caregiver_tasks
            WHERE caregiver_id = %s AND patient_id = %s ORDER BY scheduled_date DESC;
        """
        self.raw_query(query, (caregiver_id, patient_id))
        return self.fetch_all()

    def get_a_caregiver_all_tasks_info(self, caregiver_id):
        query = """
            SELECT * FROM icare.caregiver_tasks
            WHERE caregiver_id = %s ORDER BY scheduled_date DESC;
        """
        self.raw_query(query, (caregiver_id,))
        return self.fetch_all()

    def update_patient_task_status(self, task_id, status):
        query = """
            UPDATE icare.patient_tasks SET status = %s WHERE patient_task_id = %s;
        """
        self.raw_query(query, (status, task_id))
        self.commit()

    def update_caregiver_task_status(self, task_id, status):
        try:
            query = """
                UPDATE icare.caregiver_tasks SET status = %s WHERE caregiver_task_id = %s;
            """
            self.raw_query(query, (status, task_id))
            self.commit()
            return True
        except Exception as e:
            print(f"Error updating caregiver task status: {e}")
            return False

    def add_caregiver_task(self, task_description, scheduled_date, assigned_by, caregiver_id, patient_id):
        try:
            self.raw_query("""
                INSERT INTO icare.caregiver_tasks 
                (task_description, scheduled_date, status, assigned_by, caregiver_id, patient_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (task_description, scheduled_date, 'Pending', assigned_by, caregiver_id, patient_id))
            self.commit()
            return True
        except Exception as e:
            print(f"Error adding caregiver task: {e}")
            return False

    def add_patient_task(self, task_description, scheduled_date, assigned_by, patient_id):
        try:
            self.raw_query("""
                INSERT INTO icare.patient_tasks 
                (task_description, scheduled_date, status, assigned_by, assigned_for)
                VALUES (%s, %s, %s, %s, %s)
            """, (task_description, scheduled_date, 'Pending', assigned_by, patient_id))
            self.commit()
            return True
        except Exception as e:
            print(f"Error adding patient task: {e}")
            return False
        
    def insert_sensor_waveform(self, device_id, waveform_values, peaks):
        try:
            self.raw_query("""
                INSERT INTO icare.sensor_waveform (device_id, waveform_values, peaks)
                VALUES (%s, %s, %s);
            """, (device_id, waveform_values, peaks))
            self.commit()
            return True
        except Exception as e:
            print(f"Error inserting waveform data: {e}")
        return False
    
    def get_today_step_count(self, patient_id):
        query = """
            SELECT SUM(step_count)
            FROM icare.step_counting
            WHERE patient_id = %s AND date = CURRENT_DATE;
        """
        self.raw_query(query, (patient_id,))
        result = self.fetch_one()
        return result[0] if result and result[0] is not None else 0

    # ---------------------------------------------------------
    # Table Creation Functions
    # ---------------------------------------------------------
    def create_doctors(self):
        self.raw_query("""
            CREATE TABLE IF NOT EXISTS icare.doctors (
                doctor_id VARCHAR(7) PRIMARY KEY,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                phone_number VARCHAR(25) NOT NULL,
                address TEXT
            );
        """)
        self.commit()

    def create_patients(self):
        self.raw_query("""
            CREATE TABLE IF NOT EXISTS icare.patients (
                patient_id VARCHAR(25) PRIMARY KEY,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                phone_number VARCHAR(25) NOT NULL,
                address TEXT,
                doctor_id VARCHAR(7),
                caregiver_id VARCHAR(25),
                CONSTRAINT fk_doctor FOREIGN KEY (doctor_id)
                    REFERENCES icare.doctors(doctor_id) ON UPDATE CASCADE ON DELETE CASCADE
            );
        """)
        self.commit()

    def create_caregivers(self):
        self.raw_query("""
            CREATE TABLE IF NOT EXISTS icare.caregivers (
                caregiver_id VARCHAR(25) PRIMARY KEY,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                phone_number VARCHAR(25) NOT NULL,
                address TEXT
            );
        """)
        self.commit()

    def create_patient_tasks(self):
        self.raw_query("""
            CREATE TABLE IF NOT EXISTS icare.patient_tasks (
                patient_task_id SERIAL PRIMARY KEY,
                task_description TEXT NOT NULL,
                scheduled_date TIMESTAMP NOT NULL,
                status VARCHAR(20) DEFAULT 'Pending',
                assigned_by VARCHAR(7) NOT NULL,
                assigned_for VARCHAR(25) NOT NULL,
                CONSTRAINT fk_doctor FOREIGN KEY (assigned_by)
                    REFERENCES icare.doctors(doctor_id) ON UPDATE CASCADE ON DELETE CASCADE
            );
        """)
        self.commit()

    def create_caregiver_tasks(self):
        self.raw_query("""
            CREATE TABLE IF NOT EXISTS icare.caregiver_tasks (
                caregiver_task_id SERIAL PRIMARY KEY,
                task_description TEXT NOT NULL,
                scheduled_date TIMESTAMP NOT NULL,
                status VARCHAR(20) DEFAULT 'Pending',
                assigned_by VARCHAR(7) NOT NULL,
                caregiver_id VARCHAR(7) NOT NULL,
                patient_id VARCHAR(25) NOT NULL,
                CONSTRAINT fk_doctor FOREIGN KEY (assigned_by)
                    REFERENCES icare.doctors(doctor_id) ON UPDATE CASCADE ON DELETE CASCADE,
                CONSTRAINT fk_caregiver FOREIGN KEY (caregiver_id)
                    REFERENCES icare.caregivers(caregiver_id) ON UPDATE CASCADE ON DELETE CASCADE
            );
        """)
        self.commit()

    def create_task_followups(self):
        self.raw_query("""
            CREATE TABLE IF NOT EXISTS icare.task_followups (
                followup_id SERIAL PRIMARY KEY,
                task_id INTEGER NOT NULL,
                doctor_id VARCHAR(7) NOT NULL,
                message TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_task FOREIGN KEY (task_id)
                    REFERENCES icare.caregiver_tasks(caregiver_task_id) ON UPDATE CASCADE ON DELETE CASCADE,
                CONSTRAINT fk_doctor FOREIGN KEY (doctor_id)
                    REFERENCES icare.doctors(doctor_id) ON UPDATE CASCADE ON DELETE CASCADE
            );
        """)
        self.commit()

    def create_devices(self):
        self.raw_query("""
            CREATE TABLE IF NOT EXISTS icare.devices (
                device_id VARCHAR(20) PRIMARY KEY,
                battery_percentage FLOAT NOT NULL
            );
        """)
        self.commit()

    def create_patient_device(self):
        self.raw_query("""
            CREATE TABLE IF NOT EXISTS icare.patient_device (
                patient_id VARCHAR(10) NOT NULL,
                device_id VARCHAR(20) NOT NULL UNIQUE,
                linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_patient FOREIGN KEY (patient_id)
                    REFERENCES icare.patients(patient_id) ON DELETE CASCADE ON UPDATE CASCADE,
                CONSTRAINT fk_device FOREIGN KEY (device_id)
                    REFERENCES icare.devices(device_id) ON DELETE CASCADE ON UPDATE CASCADE,
                PRIMARY KEY (patient_id, device_id)
            );
        """)
        self.commit()

    def create_step_counting(self):
        self.raw_query("""
            CREATE TABLE IF NOT EXISTS icare.step_counting (
                step_id SERIAL PRIMARY KEY,
                device_id VARCHAR(20) NOT NULL,
                patient_id VARCHAR(25) NOT NULL,
                date DATE DEFAULT CURRENT_DATE,
                time_seconds BIGINT NOT NULL,
                step_count INT NOT NULL,
                acceleration_mag FLOAT NOT NULL,
                CONSTRAINT fk_device FOREIGN KEY (device_id)
                    REFERENCES icare.devices(device_id) ON DELETE CASCADE ON UPDATE CASCADE,
                CONSTRAINT fk_patient FOREIGN KEY (patient_id)
                    REFERENCES icare.patients(patient_id) ON DELETE CASCADE ON UPDATE CASCADE
            );
        """)
        self.commit()

    def create_gyroscope(self):
        self.raw_query("""
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
        self.commit()

    def create_accelerometer(self):
        self.raw_query("""
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
        self.commit()

    def create_fall_detection(self):
        self.raw_query("""
            CREATE TABLE IF NOT EXISTS icare.fall_detection (
                fall_detection_id SERIAL PRIMARY KEY,
                device_id VARCHAR(20) NOT NULL,
                fall_detected BOOLEAN NOT NULL,
                time_of_fall BIGINT NOT NULL,
                latitude DOUBLE PRECISION NOT NULL,
                longitude DOUBLE PRECISION NOT NULL,
                CONSTRAINT fk_device FOREIGN KEY (device_id)
                    REFERENCES icare.devices(device_id) ON DELETE CASCADE ON UPDATE CASCADE
            );
        """)
        self.commit()

    def create_heart_rate(self):
        self.raw_query("""
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
        self.commit()

    def create_spo2(self):
        self.raw_query("""
            CREATE TABLE IF NOT EXISTS icare.spo2 (
                spo2_id SERIAL PRIMARY KEY,
                device_id VARCHAR(20) NOT NULL,
                time_seconds BIGINT NOT NULL,
                spo2_percent INT NOT NULL,
                CONSTRAINT fk_device FOREIGN KEY (device_id)
                    REFERENCES icare.devices(device_id) ON DELETE CASCADE ON UPDATE CASCADE
            );
        """)
        self.commit()

    def create_temperature(self):
        self.raw_query("""
            CREATE TABLE IF NOT EXISTS icare.temperature (
                temperature_id SERIAL PRIMARY KEY,
                device_id VARCHAR(20) NOT NULL,
                temperature FLOAT NOT NULL,
                time_seconds BIGINT NOT NULL,
                CONSTRAINT fk_device FOREIGN KEY (device_id)
                    REFERENCES icare.devices(device_id) ON DELETE CASCADE ON UPDATE CASCADE
            );
        """)
        self.commit()

    def create_sensor_data_table(self):
        self.raw_query("""
            CREATE TABLE IF NOT EXISTS icare.sensor_data (
                id SERIAL PRIMARY KEY,
                device_id VARCHAR(20) NOT NULL,
                heart_rate INT,
                spo2 INT,
                temperature FLOAT,
                step_count INT,
                fall_detected BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.commit()

    def create_sensor_waveform_table(self):
        self.raw_query("""
            CREATE TABLE IF NOT EXISTS icare.sensor_waveform (
                waveform_id SERIAL PRIMARY KEY,
                device_id VARCHAR(20) NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                waveform_values FLOAT[] NOT NULL,
                peaks INT[] NOT NULL,
                CONSTRAINT fk_device FOREIGN KEY (device_id)
                    REFERENCES icare.devices(device_id) ON DELETE CASCADE ON UPDATE CASCADE
            );
        """)
        self.commit()

    def create_fall_detection_table(self):
        self.raw_query("""
            CREATE TABLE IF NOT EXISTS icare.fall_detection (
                fall_detection_id SERIAL PRIMARY KEY,
                device_id VARCHAR(20) NOT NULL,
                fall_detected BOOLEAN NOT NULL,
                time_of_fall BIGINT NOT NULL,
                latitude FLOAT,
                longitude FLOAT,
                CONSTRAINT fk_device FOREIGN KEY (device_id)
                    REFERENCES icare.devices(device_id) ON DELETE CASCADE ON UPDATE CASCADE
            );
        """)
        self.commit()

    # ---------------------------------------------------------
    # Reset & Create All Tables
    # ---------------------------------------------------------
    def reset(self):
        self.raw_query("""
            DROP TABLE IF EXISTS 
            icare.doctors,
            icare.patients,
            icare.caregivers,
            icare.patient_tasks,
            icare.caregiver_tasks,
            icare.task_followups,
            icare.heart_rate,
            icare.gyroscope,
            icare.accelerometer,
            icare.spo2,
            icare.step_counting,
            icare.temperature,
            icare.fall_detection,
            icare.patient_device,
            icare.devices,
            icare.sensor_waveform,
            icare.fall_detection,           
            icare.sensor_data CASCADE;
        """)
        self.commit()

    def create_all_tables(self):
        self.create_doctors()
        self.create_patients()
        self.create_caregivers()
        self.create_patient_tasks()
        self.create_caregiver_tasks()
        self.create_task_followups()
        self.create_devices()
        self.create_patient_device()
        self.create_step_counting()
        self.create_gyroscope()
        self.create_accelerometer()
        self.create_fall_detection()
        self.create_heart_rate()
        self.create_spo2()
        self.create_temperature()
        self.create_sensor_data_table()
        self.create_sensor_waveform_table()
        self.create_fall_detection_table()

    # ---------------------------------------------------------
    # Data Seeding (Optional, this is for testing)
    # ---------------------------------------------------------
    def seed_data(self):
        # Seed a dummy doctor if none exists
        self.raw_query("SELECT COUNT(*) FROM icare.doctors;")
        count = self.fetch_one()[0]
        if count == 0:
            doctor_id = "DOC0001"
            self.raw_query("""
                INSERT INTO icare.doctors (doctor_id, first_name, last_name, email, password, phone_number, address)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (doctor_id, "Alice", "Smith", "doctor@healthapp.com", "password", "1234567890", "123 Health St."))
            self.commit()
            print("Seeded dummy doctor.")

        # Seed a dummy patient if none exists
        self.raw_query("SELECT COUNT(*) FROM icare.patients;")
        patient_count = self.fetch_one()[0]
        if patient_count == 0:
            patient_id = "PAT_001"
            self.raw_query("""
                INSERT INTO icare.patients 
                (patient_id, first_name, last_name, email, password, phone_number, address, doctor_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """, (patient_id, "John", "Doe", "john.doe@healthapp.com", "password", "5551234567", "456 Patient Rd.", "DOC0001"))
            self.commit()
            print("Seeded dummy patient.")

        # Seed a default device if it doesn't exist yet
        self.raw_query("SELECT COUNT(*) FROM icare.devices WHERE device_id = %s;", ("ESP32_001",))
        device_count = self.fetch_one()[0]
        if device_count == 0:
            self.raw_query("""
                INSERT INTO icare.devices (device_id, battery_percentage)
                VALUES (%s, %s);
            """, ("ESP32_001", 100.0))
            self.commit()
            print("Seeded default device ESP32_001.")

        # Seed a mapping in patient_device (assign the device to the dummy patient)
        self.raw_query("SELECT COUNT(*) FROM icare.patient_device WHERE device_id = %s;", ("ESP32_001",))
        mapping_count = self.fetch_one()[0]
        if mapping_count == 0:
            self.raw_query("""
                INSERT INTO icare.patient_device (patient_id, device_id)
                VALUES (%s, %s);
            """, ("PAT_001", "ESP32_001"))
            self.commit()
            print("Assigned device ESP32_001 to patient PAT_001.")

        # Seed a sample sensor data row for testing for ESP32_001
        self.raw_query("SELECT COUNT(*) FROM icare.sensor_data WHERE device_id = %s;", ("ESP32_001",))
        sensor_count = self.fetch_one()[0]
        if sensor_count == 0:
            self.raw_query("""
                INSERT INTO icare.sensor_data (device_id, heart_rate, spo2, temperature, step_count)
                VALUES (%s, %s, %s, %s, %s);
            """, ("ESP32_001", 75, 98, 36.5, 1200))
            self.commit()
            print("Seeded sample sensor data for ESP32_001.")

# Instantiate the DB and connect
db = DB(dbname, user, password, host, port, schema)
db.new_connection()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == 'reset':
            db.reset()
            print("Reset successful, ready for data generation.")
            db.close()
            db.new_connection()
        elif arg == 'generate':
            db.create_all_tables()
            print("Tables creation completed successfully!")
            db.seed_data()
    else:
        print("No command provided. Use 'reset' or 'generate'.")