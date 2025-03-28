
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
        doctor_id=None
        try:
            # Assuming user table is in the schema 
            self.cursor.execute("""
                INSERT INTO icare.patients (patient_id,first_name,last_name, email, password,phone_number,address,doctor_id,caregiver_id) 
                VALUES (%s, %s, %s,%s,%s,%s,%s,%s,%s)
            """, (patient_id, firstname, lastname, email, password,phone_number,adress,None,None))
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
  def get_patient_by_id(self, patient_id):
    try:
        # Use parameterized query to avoid SQL injection
        self.cursor.execute("SELECT * FROM icare.patients WHERE patient_id = %s", (patient_id,))
        
        # Fetch the result (this will return a single row if the patient exists)
        patient = self.cursor.fetchone()
        
        # Return the patient data (None if no patient is found)
        return patient
    except Exception as e:
        # Log the error or raise it
        print(f"Error fetching patient by ID: {e}")
        return None
      
  def get_patient_name(self, patient_id):
    try:
        # Use parameterized query to avoid SQL injection
        self.cursor.execute("SELECT fist_name, last_name FROM icare.patients WHERE patient_id = %s", (patient_id,))
        
        # Fetch the result (this will return a single row if the patient exists)
        patient = self.cursor.fetchall()
        
        # Return the patient data (None if no patient is found)
        return patient
    
    except Exception as e:
        # Log the error or raise it
        print(f"Error fetching patient by ID: {e}")
        return None
      
    
  def remove_doctor_for_patient(self, doctor_id, patient_id):
    try:
        # First, check if the patient exists and fetch the current doctor_id
        self.cursor.execute("SELECT doctor_id FROM icare.patients WHERE patient_id = %s", (patient_id,))
        
        # Fetch the result (this will return a single row if the patient exists)
        patient = self.cursor.fetchone()

        if patient:  # Patient exists
            current_doctor_id = patient[0]
            
            # Check if the patient is assigned to the doctor we're trying to remove
            if current_doctor_id == doctor_id:
                # Update the doctor_id to 'XXXXXXX' for the patient
                self.cursor.execute("UPDATE icare.patients SET doctor_id = %s WHERE patient_id = %s", (None,patient_id))
                
                # Commit the change to the database
                self.connection.commit()  # Assuming `self.connection` is the DB connection object

                return True  # Return True to indicate the update was successful
            else:
                # If the current doctor_id doesn't match the doctor we're removing, return False
                return False  # The patient is not assigned to the provided doctor_id
        else:
            # If the patient doesn't exist, return False
            return False  # Patient does not exist
    
    except Exception as e:
        # Log the error or raise it
        print(f"Error removing doctor for patient: {e}")
        return None



    
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
    
    # Fetch the result (if exists)
    doctor_name = self.cursor.fetchone()
    
    # If no doctor was found, doctor_name will be None, so handle that appropriately
    if doctor_name:
        return doctor_name[0]  # Return the first name from the result
    else:
        return None  # Or handle it as appropriate for your case

  def get_doctor_name(self, doctor_id):
    # Use parameterized query to avoid SQL injection
    self.cursor.execute("SELECT first_name FROM icare.doctors WHERE doctor_id = %s", (doctor_id,))
    
  def get_the_doctor_patients(self, doctor_id):
    try:
        # Use parameterized query to avoid SQL injection
        self.cursor.execute("SELECT * FROM icare.patients WHERE doctor_id = %s", (doctor_id,))
        
        # Fetch all the rows for the given doctor_id
        patients = self.cursor.fetchall()
        
        # Return the result, or you can process it further if needed
        return patients # This will return a list of tuples, where each tuple is a patient's data
    
    except Exception as e:
        # Log the error or raise it
        print(f"Error fetching doctor patients: {e}")
        return None
  
  def doctor_Add_patient(self, doctor_id, patient_id):
    try:
        # Use parameterized query to check if the patient exists
        self.cursor.execute("SELECT patient_id FROM icare.patients WHERE patient_id = %s", (patient_id,))
        
        # Fetch the result (this will return a list of tuples)
        result = self.cursor.fetchall()

        if result:  # Patient exists
            # Check if doctor_id is valid
            if doctor_id is None:
                print("Error: Invalid doctor_id")
                return False

            # Use parameterized query to associate the doctor with the patient
            self.cursor.execute("UPDATE icare.patients SET doctor_id = %s WHERE patient_id = %s AND doctor_id IS NULL", (doctor_id, patient_id))
            
            # Commit the change to the database
            self.connection.commit()
            
            # Verify the update
            self.cursor.execute("SELECT doctor_id FROM icare.patients WHERE patient_id = %s", (patient_id,))
            updated_doctor_id = self.cursor.fetchone()
            
            if updated_doctor_id and updated_doctor_id[0] == doctor_id:
                return True  # Successfully updated doctor_id
            else:
                print("Error: Failed to update doctor_id.")
                return False
        else:
            return False  # Patient does not exist

    except Exception as e:
        print(f"Error adding patient to doctor: {e}")
        return None

 
    
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
      
  def get_caregiver_tasks(self, caregiver_id, patient_id):
    query = """
        SELECT task_description,status
        FROM icare.caregiver_tasks
        WHERE caregiver_id = %s AND patient_id = %s
        ORDER BY scheduled_date DESC;
    """
    self.cursor.execute(query, (caregiver_id,patient_id,))
    return self.cursor.fetchall()
  

      
  def add_caregiver_task(self, task_description, scheduled_date, assigned_by, caregiver_id, patient_id):
    try:
        # Insert a new caregiver task into the icare.caregiver_tasks table
        self.cursor.execute("""
            INSERT INTO icare.caregiver_tasks (task_description, scheduled_date, status, assigned_by, caregiver_id, patient_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (task_description, scheduled_date, 'Pending', assigned_by, caregiver_id, patient_id))

        # Commit the transaction to save the changes
        self.connection.commit()

        # Return True to indicate that the task was successfully added
        return True
    except Exception as e:
        # Log any exceptions or errors that occurred
        print(f"Error adding caregiver task: {e}")
        return False
      
      
  def add_patient_task(self, task_description, scheduled_date, assigned_by, patient_id):
    try:
        # Insert a new caregiver task into the icare.caregiver_tasks table
        self.cursor.execute("""
            INSERT INTO icare.patient_tasks (task_description, scheduled_date, status, assigned_by, assigned_for)
            VALUES (%s, %s, %s, %s, %s)
        """, (task_description, scheduled_date, 'Pending', assigned_by,  patient_id))

        # Commit the transaction to save the changes
        self.connection.commit()

        # Return True to indicate that the task was successfully added
        return True
    except Exception as e:
        # Log any exceptions or errors that occurred
        print(f"Error adding caregiver task: {e}")
        return False



 

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
  
  def update_phone_number_of_doctors(self, doctor_id, phone_number):
    self.cursor.execute(f"UPDATE icare.doctors_phone_numbers SET phone_number = '{phone_number}' WHERE doctor_id = '{doctor_id}'")


  
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
        SELECT task_description,status
        FROM icare.patient_tasks
        WHERE assigned_for = %s
        ORDER BY scheduled_date DESC;
    """
    self.cursor.execute(query, (patient_id,))
    return self.cursor.fetchall()
  
  def get_patient_tasks_Info(self, patient_id):
    query = """
        SELECT *
        FROM icare.patient_tasks
        WHERE assigned_for = %s
        ORDER BY scheduled_date DESC;
    """
    self.cursor.execute(query, (patient_id,))
    return self.cursor.fetchall()
  
  def get_caregiver_tasks_Info(self, caregiver_id, patient_id):
    query = """
        SELECT *
        FROM icare.caregiver_tasks
        WHERE caregiver_id = %s AND patient_id = %s
        ORDER BY scheduled_date DESC;
    """
    self.cursor.execute(query, (caregiver_id, patient_id))
    return self.cursor.fetchall()
  
  def get_a_caregiver_All_tasks_Info(self, patient_id):
    query = """
        SELECT *
        FROM icare.caregiver_tasks
        WHERE caregiver_id = %s 
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
    try:
      query = """
        UPDATE icare.caregiver_tasks
        SET status = %s
        WHERE caregiver_task_id = %s;
      """
      self.cursor.execute(query, (status, task_id))
      self.connection.commit()
      return True
    except Exception as e:
        # Log any exceptions or errors that occurred
        print(f"Error adding caregiver task: {e}")
        return False

db = DB(dbname, user, password, host, port, schema)
db.new_connection()

