from Utils.logger import get_module_logger
import clickhouse_connect
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
        """
        runs a query on MySQL and commits it
        :param query:
        :param var:
        :return:
        """
        try:
            self.cursor.execute(query, var)
            self.db.commit()
        except Exception as e:
            get_module_logger("MySQL").error(e)

    def select(self, query, var=()):
        """
        runs a query on MySQL and returns its fetch output
        :param query:
        :param var:
        :return:
        """
        try:
            self.cursor.execute(query, var)
            return self.cursor.fetchall()
        except Exception as e:
            get_module_logger("MySQL").error(e)
            return []

    def close_connection(self):
        """
        closes connection to MySQL
        :return:
        """
        self.cursor.close()
        self.db.close()


class ClickHouse:

    def __init__(self):
        client = clickhouse_connect.get_client(
            host=os.environ['CH_HOST'],
            username=os.environ['CH_USER'],
            password=os.environ['CH_PASS'])
        self.client = client
        self.fail_counter = 0

    def select(self, query, params={}):
        """
        runs query on Clickhouse and returns its row based result
        :param query:
        :param params:
        :return:
        """
        try:
            result = self.client.query(query=query, parameters=params)
            return result.result_rows
        except Exception as e:
            get_module_logger("ClickHouse").error(str(e))

    def query(self, query, params={}):
        """
        runs a query on Clickhouse
        :param query:
        :param params:
        :return:
        """
        try:
            self.client.query(query=query, parameters=params)
            return
        except Exception as e:
            get_module_logger("ClickHouse").error(str(e))
