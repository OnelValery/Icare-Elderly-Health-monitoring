import psycopg2

class DBConnection:
  def __init__(self, dbname, user, password, host, port, schema):
    self.connection = psycopg2.connect(dbname = dbname, user = user, password = password, host = host, port = port)
    self.cursor = self.connection.cursor()
    self.schema = schema
    self.cursor.execute(f"SET search_path = {schema}")
  
  def close(self):
    self.connection.close()

  def commit(self):
    self.connection.commit()

def new_connection(dbname, user, password, host, port, schema):
  connection = DBConnection(dbname, user, password, host, port, schema)
  return connection