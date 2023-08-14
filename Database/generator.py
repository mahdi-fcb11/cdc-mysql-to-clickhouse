from Utils.logger import get_module_logger
from Utils.db_connection import MySQL
from faker import Faker
from time import sleep
import random


class Generator:
    def __init__(self):
        self.db = MySQL()
        self.fake = Faker()

    def generate_data(self):
        """
        This function uses Faker to output random name, birthdate and email
        :return:
        """
        profile = self.fake.simple_profile()
        name = profile["name"]
        birthdate = profile["birthdate"]
        email = profile["mail"]
        return name, birthdate, email

    def insert(self):
        """
        This function inserts the data from generate_data function into users table
        :return:
        """
        query = """
            INSERT INTO users (name, birthdate, created_at, updated_at, email)
            VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s)
        """
        var = self.generate_data()
        self.db.query(query, var)
        get_module_logger("Database").info("inserted a new data")

    def update(self):
        """
        This function updates a random id in users table and adds an address to this user
        :return:
        """
        query = "SELECT id FROM users"
        idx = self.db.select(query)
        up_id = random.choice(idx)[0]
        address = self.fake.address()
        update_query = "UPDATE users SET address = (%s), updated_at = CURRENT_TIMESTAMP WHERE id = (%s)"
        self.db.query(update_query, (address, up_id))
        get_module_logger("Database").info(f"updated data with id = {up_id}.")

    def delete(self):
        """
        This function selects a random user and deletes it
        :return:
        """
        query = "SELECT id FROM users"
        idx = self.db.select(query)
        del_id = random.choice(idx)[0]
        delete_query = "DELETE FROM users WHERE id = (%s)"
        self.db.query(delete_query, (del_id,))
        get_module_logger("Database").info(f"deleted data with id = {del_id}")

    def runner(self):
        """
        This function randomly selects between insert, delete and update functions and runs it
        :return:
        """
        chosen = random.choices(
            [self.update, self.delete, self.insert], weights=(0.25, 0.05, 0.7), k=1
        )[0]
        chosen()


if __name__ == '__main__':
    # We run generator runner infinitely to insert random data to users table
    generator = Generator()
    while True:
        generator.runner()
        sleep(5)
