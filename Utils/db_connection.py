import mysql.connector
import os


class MySQL:

    def __init__(self):
        self.db = mysql.connector.connect(
            host=os.environ['MYSQL_HOST'],
            user="root",
            password=os.environ['MYSQL_ROOT_PASS'],
            database=os.environ['MYSQL_DB'],
            port=os.environ['MYSQL_PORT'])
        self.cursor = self.db.cursor()

    def query(self, query, var=()):
        try:
            self.cursor.execute(query, var)
            self.db.commit()
        except Exception as e:
            print("Could not execute query: ", e)

    def select(self, query, var=()):
        try:
            self.cursor.execute(query, var)
            return self.cursor.fetchall()
        except Exception as e:
            print("Could not execute query: ", e)
            return []

    def close_connection(self):
        self.cursor.close()
        self.db.close()
