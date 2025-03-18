
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
  def raw_query(self, query):
    self.cursor.execute(query)


  #employee
  def get_employee(self, employee_sin):
      self.cursor.execute(f"select * from project.employees where employee_sin='{employee_sin}'")

  def delete_employee(self, employee_sin):
      self.cursor.execute(f"delete from project.employees where employee_sin='{employee_sin}'")
  
  def update_employee(self, employee_sin, updatepart,upvalue):
    sql="UPDATE project.employees SET "+updatepart+" = '"+upvalue+"' where employee_sin = '"+employee_sin+"'"
    self.cursor.execute(sql)
  
  def check_employee(self, employee_id):
    self.cursor.execute(f"select count(employee_id) from project.employees where employee_id='{employee_id}'")
  
  def get_search_employees(self, employee_sin, completname,hotel_id, province,title):
    self.cursor.execute(f"""select * from project.employees where employee_sin='{employee_sin}' or completname='{completname}' or province='{province}' or hotel_id='{hotel_id}' or title='{title}'""")

  def get_password_from_employee(self, employee_sin):
    self.cursor.execute(f"select password from project.employees where employee_sin='{employee_sin}'")
  
  def get_title(self, employee_id):
    self.cursor.execute(f" select title from employees where employee_id='{employee_id}' ")

  def get_manager(self, hotel_id):
    self.cursor.execute(f" select manager from hotels where hotel_id='{hotel_id}' ")


  def view_employees_per_hotel(self, hotel_id):
    self.cursor.execute(f""" select * from employees where hotel_id='{hotel_id}' """)

  def assign_employee_to_property(self, employeeusername, propertyname):
    self.cursor.execute(f""" insert into works_at (employeeusername, propertyname) values ('{employeeusername}', '{propertyname}')  """)

  def get_employee_country(self, employeeusername):
    self.cursor.execute(f""" select country from employees where username='{employeeusername}'  """)

 
  def insert_phone_number(self, username, phone_number):
    self.cursor.execute(f"insert into person_phone_number (username, phone_number) VALUES ('{username}', '{phone_number}')")
  
  def update_phone_number(self, username, phone_number):
    self.cursor.execute(f"UPDATE hotels_phone_number SET phone_number = '{phone_number}' WHERE hotel_id = '{username}'")


  #users
  def check_totalUser(self):
    self.cursor.execute(f"select count(customer_id) from project.customers")
  
 
  def get_verified(self, username):
    self.cursor.execute(f"select verified from users where username='{username}'")

 
  #Hotels
  def get_hotel(self, hotel_id):
      self.cursor.execute(f"select * from project.hotels where hotel_id='{hotel_id}'")
  
  def get_search_All_Hotels(self):
      self.cursor.execute(f"select * from project.hotels")
  
  
  def get_hotel_id(self):     #Important
    self.cursor.execute(f""" select hotel_id from project.hotels """)
  
  def delete_hotel(self, hotel_id):
      self.cursor.execute(f"delete from project.hotels where hotel_id='{hotel_id}'")
    
  def update_hotel(self, hotel_id, updatepart,upvalue):
    sql="UPDATE project.hotels SET "+updatepart+" = '"+upvalue+"' where hotel_id = '"+hotel_id+"'"
    self.cursor.execute(sql)
    
  def check_total_hotels(self):
    sql="select count(hotel_id) from project.hotels"
    self.cursor.execute(sql)
  
  
  def get_hotels_by_country(self, country):
    self.cursor.execute(f""" select hotel_name from hotels where country='{country}' """)

 
  def get_hotels_of_chain(self, chain_id):
      self.cursor.execute(f"select * from hotels where chain_id='{chain_id}'")

 #Customer
  def get_customer(self, customer_id):
      self.cursor.execute(f"select * from project.customers where customer_id='{customer_id}'")

  def delete_customer(self, customer_id):
      self.cursor.execute(f"delete from project.customers where customer_id='{customer_id}'")
  
  def update_customer(self, customer_id, updatepart,upvalue):
    sql="UPDATE project.customers SET "+updatepart+" = '"+upvalue+"' where customer_id = '"+customer_id+"'"
    self.cursor.execute(sql)
    
  def get_search_customers(self, customer_id, completname,hotel_id, country):
      self.cursor.execute(f"""select * from project.customers where customer_id='{customer_id}' or completname='{completname}' or country='{country}' or hotel_id='{hotel_id}'""")
  
  def get_password_from_customer(self, customer_id):
    self.cursor.execute(f"select password from project.customers where customer_id='{customer_id}'")

  
  
  
  def valid_chain_hotel_number(self, chain_id):
    self.cursor.execute(f"select count(hotel_name) from project.hotels where chain_id='{chain_id}'")

  def create_hotel(self, hotel_name, street_number, street_name, apt_number, postal_code, rent_rate, country, province, property_type, max_guests, number_beds, number_baths, accessible, pets_allowed, current_user_id, picture):
    self.cursor.execute(f"insert into project.hotels (hotel_name, street_number, street_name, apt_number, province, postal_code,  number_beds, accessible, pets_allowed, country, hostusername, picture) VALUES ('{property_name}', '{street_number}', '{street_name}', '{apt_number}', '{province}', '{postal_code}', '{rent_rate}', '{property_type}', '{max_guests}', '{number_beds}', '{number_baths}', '{accessible}', '{pets_allowed}', '{country}', '{current_user_id}', '{picture}')")

  def get_search_hotels(self, chain_id, hotel_id, hotel_name, country, province,postal_code, ranking):
      self.cursor.execute(f"""select * from project.hotels where chain_id='{chain_id}' or hotel_name='{hotel_name}' or country='{country}' or province='{province}' or postal_code='{postal_code}' 
      or hotel_id='{hotel_id}' or ranking='{ranking}'""")



  def get_short_term_unavailable_hotels(self, country):
    join_date = datetime.datetime.today()
    tomorrow = join_date + datetime.timedelta(days=1)
    next_day = join_date + datetime.timedelta(days=1)
    join_date = join_date.strftime('%Y-%m-%d')
    tomorrow = tomorrow.strftime('%Y-%m-%d')
    next_day = next_day.strftime('%Y-%m-%d')
    self.cursor.execute(f""" select * from hotels as P where exists(select * from hotels_taken_dates as PT where PT.hotel_name=P.propertyname and
                        (PT.taken_date='{join_date}' or PT.taken_date='{tomorrow}' or
                        PT.taken_date='{next_day}')) and P.country='{country}'  """)
 
  #reservations
  def get_reservation(self, reservation_id):
      self.cursor.execute(f"select * from project.reservations where reservation_id='{reservation_id}'")
  
  def get_customer_reservation(self, customer_id):
      self.cursor.execute(f"select * from project.reservations where customer_id='{customer_id}'")
  
  
  def update_reservation(self, reservation_id, updatepart,upvalue):
    sql="UPDATE project.reservations SET "+updatepart+" = '"+upvalue+"' where reservation_id = '"+reservation_id+"'"
    self.cursor.execute(sql)
    
  def delete_reservation(self, reservation_id):
      self.cursor.execute(f"delete from project.reservations where reservation_id='{reservation_id}'")
      
    
  
  
  def get_total_completed_stays(self):
    self.cursor.execute(f"select count(reservation_id) from project.reservations where reservation_status='approved'")
  def get_room_numbers(self,hotel_id,availability):
    self.cursor.execute(f"select room_number from project.rooms where hotel_id='{hotel_id}'and availability ='{availability}'")
  
  #chains
  def get_total_countrys(self):
    self.cursor.execute(f"select count(country) from project.chains where country=country")

  def valid_country(self, country):
    self.cursor.execute(f"select count(country) from person where country='{country}'")
    
  def check_totalchain(self):
    sql="select count(chain_id) from project.chains"
    self.cursor.execute(sql)
    
  #rooms
  def get_room(self, room_number):
      self.cursor.execute(f"select * from project.rooms where room_number='{room_number}'")

  def delete_room(self, room_number):
      self.cursor.execute(f"delete from project.rooms where room_number='{room_number}'")
  
  def update_room(self, room_number, updatepart,upvalue):
    sql="UPDATE project.rooms SET "+updatepart+" = '"+upvalue+"' where room_number = '"+room_number+"'"
    self.cursor.execute(sql)
    
  def get_search_rooms(self, room_number, hotel_id):
    self.cursor.execute(f"""select * from project.rooms where room_number='{room_number}' or hotel_id='{hotel_id}' """)

  def get_search_All_Available_rooms(self):
    self.cursor.execute(f"""select * from project.rooms where availability='Available' """)
  
  def get_search_Available_rooms(self, hotel_id):
    self.cursor.execute(f"""select * from project.rooms where availability='Available' and hotel_id='{hotel_id}' """)

    
    
    
  def check_total_rooms(self):
    sql="select count(room_number) from project.rooms"
    self.cursor.execute(sql)
  
db = DB(dbname, user, password, host, port, schema)
db.new_connection()



