
from dbconnection import new_connection
import os
import secrets
import datetime

#change these credentials to change db
dbname = "omezi035"
user = "postgres"
password = "Thaina@13"
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
    connection = new_connection(self.dbname, self.user, self.password, self.host, self.port, self.schema)
    self.connection = connection
    self.cursor = self.connection.cursor

  def close(self):
    self.connection.close()
  
  #basic db stuff
  def fetch_all(self):
    return self.cursor.fetchall()
  
  def fetch_one(self):
    return self.cursor.fetchone()

  def commit(self):
    self.connection.commit()

  #doctor
  def register_doctor(self,doctor_id, firstname, lastname, phone_number, email, password,adress):
      
        try:
            # Assuming user table is in the schema 
            self.cursor.execute("""
                INSERT INTO icare.doctors (doctor_id,first_name,last_name, email, password,phone_number,address) 
                VALUES (%s, %s, %s,%s,%s,%s,%s)
            """, (doctor_id, firstname, lastname, email, password,phone_number,adress))
            self.commit()
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False
          
  def valid_doctor_account(self, email, password):
        try:
            self.cursor.execute("""
                SELECT email, password FROM icare.doctors 
                WHERE email = %s AND password = %s
            """, (email, password))
            result = self.fetch_one()

            if result:
                return True  # Account found and valid
            else:
                return False  # Invalid credentials
        except Exception as e:
            print(f"Error validating account: {e}")
            return False
  #register caregivers
  def register_caregiver(self,caregiver_id, firstname, lastname, phone_number, email, password,adress):
      
        try:
            # Assuming user table is in the schema 
            self.cursor.execute("""
                INSERT INTO icare.caregivers (caregiver_id,first_name,last_name, email, password,phone_number,address) 
                VALUES (%s, %s, %s,%s,%s,%s,%s)
            """, (caregiver_id, firstname, lastname, email, password, phone_number,adress))
            self.commit()
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False
          
  def valid_caregiver_account(self, email, password):
        try:
            self.cursor.execute("""
                SELECT email, password FROM icare.caregivers 
                WHERE email = %s AND password = %s
            """, (email, password))
            result = self.fetch_one()

            if result:
                return True  # Account found and valid
            else:
                return False  # Invalid credentials
        except Exception as e:
            print(f"Error validating account: {e}")
            return False
  
# register patient
  def register_patient(self,patient_id, firstname, lastname, phone_number, email, password,adress):
        doctor_id='0000000'
        try:
            # Assuming user table is in the schema 
            self.cursor.execute("""
                INSERT INTO icare.patients (patient_id,first_name,last_name, email, password,phone_number,address,doctor_id) 
                VALUES (%s, %s, %s,%s,%s,%s,%s,%s)
            """, (patient_id, firstname, lastname, email, password,phone_number,adress,doctor_id))
            self.commit()
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False
          
  def valid_patient_account(self, email, password):
        try:
            self.cursor.execute("""
                SELECT email, password FROM icare.patients 
                WHERE email = %s AND password = %s
            """, (email, password))
            result = self.fetch_one()

            if result:
                return True  # Account found and valid
            else:
                return False  # Invalid credentials
        except Exception as e:
            print(f"Error validating account: {e}")
            return False

  #raw query
  '''
  def raw_query(self, query):
    self.cursor.execute(query)
    '''
    
  def raw_query(self, query, params=None):
    """
    Execute a raw SQL query with optional parameters.
    """
    if params:
        self.cursor.execute(query, params)
    else:
        self.cursor.execute(query)

# getter Functions
  def get_patient(self, patient_id):
    self.cursor.execute(f"select * from icare.patients where patient_id ='{patient_id}'")
    
  def get_caregiver(self, caregiver_id):
    self.cursor.execute(f"select * from icare.caregivers where caregiver_id ='{caregiver_id}'")
    
  def get_doctor(self, doctor_id):
    self.cursor.execute(f"select * from icare.doctors where doctor_id ='{doctor_id}'")
    

# deleters
  def delete_caregiver(self, caregiver_id):
    self.cursor.execute(f"delete from icare.caregivers where caregiver_id ='{caregiver_id}'")
    
  def delete_doctor(self, doctor_id):
    self.cursor.execute(f"delete from icare.doctors where caregiver_id ='{doctor_id}'")
  
  def delete_patient(self, patient_id):
    self.cursor.execute(f"delete from icare.patients where caregiver_id ='{patient_id}'")
    

#Updaters
    
  def update_caregivers(self, caregiver_id, updatepart,upvalue):
    sql="UPDATE icare.caregivers SET "+updatepart+" = '"+upvalue+"' where caregiver_id = '"+caregiver_id+"'"
    self.cursor.execute(sql)
    
  def update_doctors(self, doctor_id, updatepart,upvalue):
    sql="UPDATE icare.doctors SET "+updatepart+" = '"+upvalue+"' where doctor_id = '"+doctor_id+"'"
    self.cursor.execute(sql)
  
  def update_patients(self, patient_id, updatepart,upvalue):
    sql="UPDATE icare.patients SET "+updatepart+" = '"+upvalue+"' where patient_id = '"+patient_id+"'"
    self.cursor.execute(sql)
    
    
  def get_password_from_caregivers(self, caregiver_id):
        self.cursor.execute(f"select password from icare.caregivers where caregiver_id ='{caregiver_id}'")

  def get_password_from_patients(self, patient_id):
    self.cursor.execute(f"select password from icare.patients where patient_id ='{patient_id}'")
 
  def get_password_from_doctors(self, doctor_id):
    self.cursor.execute(f"select password from icare.doctors where doctor_id ='{doctor_id}'") 

#  get email
  def get_email_from_caregivers(self, caregiver_id):
    self.cursor.execute(f"select email from icare.caregivers where caregiver_id ='{caregiver_id}'")
    
  def get_email_from_patients(self, patient_id):
    self.cursor.execute(f"select email from icare.patients where patient_id ='{patient_id}'")
 
  def get_email_from_doctors(self, doctor_id):
    self.cursor.execute(f"select email from icare.doctors where doctor_id ='{doctor_id}'") 

#  get email
  def get_phone_number_from_caregivers(self, caregiver_id):
    self.cursor.execute(f"select phone_number from icare.caregivers where caregiver_id ='{caregiver_id}'")
    
  def get_phone_number_from_patients(self, patient_id):
    self.cursor.execute(f"select phone_number from icare.patients where patient_id ='{patient_id}'")
 
  def get_phone_number_from_doctors(self, doctor_id):
    self.cursor.execute(f"select phone_number from icare.doctors where doctor_id ='{doctor_id}'") 
    
  def get_doctor_name(self, doctor_id):
    # Use parameterized query to avoid SQL injection
    self.cursor.execute("SELECT first_name FROM icare.doctors WHERE doctor_id = %s", (doctor_id,))
    
    # Fetch the result (if exists)
    doctor_name = self.cursor.fetchone()
    
    # If no doctor was found, doctor_name will be None, so handle that appropriately
    if doctor_name:
        return doctor_name[0]  # Return the first name from the result
    else:
        return None  # Or handle it as appropriate for your case

    
  def get_doctor_data(self, doctor_id):
    # Use parameterized query to avoid SQL injection
    self.cursor.execute("SELECT * FROM icare.doctors WHERE doctor_id = %s", (doctor_id,))
    
    # Fetch the result (if exists)
    doctor_data = self.cursor.fetchone()
    
    # Return the doctor data if found, or None if not found
    return doctor_data

  def get_caregiver_data(self, caregiver_id):
    # Use parameterized query to avoid SQL injection
    self.cursor.execute("SELECT * FROM icare.caregivers WHERE caregiver_id = %s", (caregiver_id,))
    
    # Fetch the result (if exists)
    caregiver_data = self.cursor.fetchone()
    
    # Return the doctor data if found, or None if not found
    return caregiver_data
  
  def get_patient_data(self, patient_id):
    # Use parameterized query to avoid SQL injection
    self.cursor.execute("SELECT * FROM icare.patients WHERE patient_id = %s", (patient_id,))
    
    # Fetch the result (if exists)
    patient_data = self.cursor.fetchone()
    
    # Return the doctor data if found, or None if not found
    return patient_data

        
  def get_doctor_id_by_email(self, email):
    # Ensure email is a valid string and strip any extra whitespace
    if isinstance(email, str):
        email = email.strip()

    # Use parameterized query to avoid SQL injection
    self.cursor.execute("SELECT doctor_id FROM icare.doctors WHERE email = %s", (email,))
    
    # Fetch and return the result (if needed)
    doctor_id = self.cursor.fetchone()
    return doctor_id[0]


  def get_patient_id_by_email(self, email):
    # Ensure email is a valid string and strip any extra whitespace
    if isinstance(email, str):
        email = email.strip()

    # Use parameterized query to avoid SQL injection
    self.cursor.execute("SELECT patient_id FROM icare.patients WHERE email = %s", (email,))
    
    # Fetch the result (if exists)
    patient_id = self.cursor.fetchone()

    # Return the patient_id if found, or None if not found
    if patient_id:
        return patient_id[0]  # Return the patient_id from the result
    else:
        return None  # Or handle it as appropriate for your case

    
  def get_caregiver_id_by_email(self, email):
    # Ensure email is a valid string and strip any extra whitespace
    if isinstance(email, str):
        email = email.strip()

    # Use parameterized query to avoid SQL injection
    self.cursor.execute("SELECT caregiver_id FROM icare.caregivers WHERE email = %s", (email,))
    
    # Fetch the result (if exists)
    caregiver_id = self.cursor.fetchone()

    # Return the caregiver_id if found, or None if not found
    if caregiver_id:
        return caregiver_id[0]  # Return the caregiver_id from the result
    else:
        return None  # Or handle it as appropriate for your case


 
 
  def insert_phone_number_of_caregivers(self, caregiver_id, phone_number):
    self.cursor.execute(f"insert into icare.caregivers_phone_numbers (caregiver_id, phone_number) VALUES ('{caregiver_id}', '{phone_number}')")
  
  def update_phone_number_of_caregivers(self, caregiver_id, phone_number):
    self.cursor.execute(f"UPDATE icare.caregivers_phone_numbers SET phone_number = '{phone_number}' WHERE caregiver_id = '{caregiver_id}'")

  def insert_phone_number_of_patients(self, patient_id, phone_number):
    self.cursor.execute(f"insert into icare.patients_phone_numbers (patient_id, phone_number) VALUES ('{patient_id}', '{phone_number}')")
  
  def update_phone_number_of_patients(self, patient_id, phone_number):
    self.cursor.execute(f"UPDATE icare.patients_phone_numbers SET phone_number = '{phone_number}' WHERE patient_id = '{patient_id}'")

  def insert_phone_number_of_doctors(self, doctor_id, phone_number):
    self.cursor.execute(f"insert into icare.doctors_phone_numbers (doctor_id, phone_number) VALUES ('{doctor_id}', '{phone_number}')")
  
  def update_phone_number_of_doctorss(self, doctor_id, phone_number):
    self.cursor.execute(f"UPDATE icare.doctors_phone_numbers SET phone_number = '{phone_number}' WHERE doctor_id = '{doctor_id}'")


  def get_caregiver_task(self, caregiver_id):
    self.cursor.execute(f""" select task_description from icare.caregivers_tasks where caregiver_id='{caregiver_id}' """)


  def get_patient_task(self, patient_id):
    self.cursor.execute(f""" select task_description from icare.patient_tasks where patient_id='{patient_id}' """)


  def get_patient_heart_rate(self, patient_id):
    query = """
        SELECT timestamp, heart_rate
        FROM icare.heart_rate
        WHERE patient_id = %s
        ORDER BY timestamp DESC;
    """
    self.cursor.execute(query, (patient_id,))
    return self.cursor.fetchall()

  def get_patient_spo2_levels(self, patient_id):
    query = """
        SELECT timestamp, spo2_level
        FROM icare.spo2
        WHERE patient_id = %s
        ORDER BY timestamp DESC;
    """
    self.cursor.execute(query, (patient_id,))
    return self.cursor.fetchall()

  def get_patient_temperature(self, patient_id):
    query = """
        SELECT timestamp, temperature
        FROM icare.temperature
        WHERE patient_id = %s
        ORDER BY timestamp DESC;
    """
    self.cursor.execute(query, (patient_id,))
    return self.cursor.fetchall()

  def get_patient_step_count(self, patient_id):
    query = """
        SELECT date, step_count
        FROM icare.step_counting
        WHERE patient_id = %s
        ORDER BY date DESC;
    """
    self.cursor.execute(query, (patient_id,))
    return self.cursor.fetchall()

  def get_patient_fall_events(self, patient_id):
    query = """
        SELECT timestamp, event_details
        FROM icare.fall_detection
        WHERE patient_id = %s
        ORDER BY timestamp DESC;
    """
    self.cursor.execute(query, (patient_id,))
    return self.cursor.fetchall()

  def get_patient_gyroscope_data(self, patient_id):
    query = """
        SELECT timestamp, x_axis, y_axis, z_axis
        FROM icare.gyroscope
        WHERE patient_id = %s
        ORDER BY timestamp DESC;
    """
    self.cursor.execute(query, (patient_id,))
    return self.cursor.fetchall()

  def get_patient_accelerometer_data(self, patient_id):
    query = """
        SELECT timestamp, x_axis, y_axis, z_axis
        FROM icare.accelerometer
        WHERE patient_id = %s
        ORDER BY timestamp DESC;
    """
    self.cursor.execute(query, (patient_id,))
    return self.cursor.fetchall()

  def get_patient_tasks(self, patient_id):
    query = """
        SELECT task_description
        FROM icare.patient_tasks
        WHERE patient_id = %s
        ORDER BY scheduled_date DESC;
    """
    self.cursor.execute(query, (patient_id,))
    return self.cursor.fetchall()

  def update_patient_task_status(self, task_id, status):
    query = """
        UPDATE icare.patient_tasks
        SET status = %s
        WHERE task_id = %s;
    """
    self.cursor.execute(query, (status, task_id))
    self.connection.commit()

  def update_caregiver_task_status(self, task_id, status):
    query = """
        UPDATE icare.caregiver_tasks
        SET status = %s
        WHERE task_id = %s;
    """
    self.cursor.execute(query, (status, task_id))
    self.connection.commit()

db = DB(dbname, user, password, host, port, schema)
db.new_connection()

