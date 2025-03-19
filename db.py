
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
schema = "Icare_project"

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

  #person
  def valid_account(self, customer_id, password):
    try:
      self.cursor.execute(f"select {customer_id} from Icare_project.doctor")
    
    except Exception as e:
      print(type(e))
      print(e)
      return (False, "Invalid Username")

    try: 
      self.cursor.execute(f"select {customer_id}, {password} from person")

    except Exception as e:
      print(type(e))
      print(e)
      return (False, "Invalid Password")
    
    return (True, "Successful Sign in")

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
    self.cursor.execute(f"select * from icare.patients where caregiver_id ='{patient_id}'")
    
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
    
# get_password
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
    self.cursor.execute(f"select phone_number from icare.caregiver_phone_numbers where caregiver_id ='{caregiver_id}'")
    
def get_phone_number_from_patients(self, patient_id):
    self.cursor.execute(f"select phone_number from icare.patient_phone_numbers where patient_id ='{patient_id}'")
 
def get_phone_number_from_doctors(self, doctor_id):
    self.cursor.execute(f"select phone_number from icare.doctor_phone_numbers where doctor_id ='{doctor_id}'") 
    

 
 
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



