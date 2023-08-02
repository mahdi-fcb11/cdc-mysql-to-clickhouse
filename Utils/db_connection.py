import mysql.connector
import os


class MySQL(mysql.connector.connect):

    def __init__(self):
        super().__init__(host="localhost", user="root", password=os.environ['MYSQL_ROOT_PASS'],
                         database=os.environ['MYSQL_DB'])

    def query(self, query, var=()):
        try:
            self.cursor.exexute(query, var)
            self.commit()
        except Exception as e:
            print("Could not execute query: ", e)

    def select(self, query, var=()):
        try:
            self.cursor.exexute(query, var)
            return self.cursor.fetchall()
        except Exception as e:
            print("Could not execute query: ", e)
            return []

    def close_connection(self):
        self.cursor.close()
        self.close()
