import psycopg2

class DBConnection:
    def __init__(self, dbname, user, password, host, port, schema):
        self.connection = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.cursor = self.connection.cursor()
        self.schema = schema
        self.cursor.execute(f"SET search_path TO {schema};")

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()

def new_connection(dbname, user, password, host, port, schema):
    return DBConnection(dbname, user, password, host, port, schema)