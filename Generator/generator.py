from Utils.db_connection import MySQL
from faker import Faker
import random


class Generator:

    def __init__(self):
        self.db = MySQL()
        self.fake = Faker()

    def generate_data(self):
        profile = self.fake.simple_profile()
        name = profile['name']
        birthdate = profile['birthdate']
        email = profile['mail']
        return name, birthdate, email

    def insert(self):
        query = """
            INSERT INTO users (name, birthdate, created_at, updated_at, email)
            VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s)
        """
        var = self.generate_data()
        self.db.query(query, var)

    def update(self):
        query = "SELECT id FROM users"
        idx = self.db.select(query)
        up_id = random.choice(idx)[0]
        address = self.fake.address()
        update_query = "UPDATE users SET address = (%s) WHERE id = (%s)"
        self.db.query(update_query, (address, up_id))

    def delete(self):
        query = "SELECT id FROM users"
        idx = self.db.select(query)
        del_id = random.choice(idx)[0]
        delete_query = "DELETE FROM users WHERE id = (%s)"
        self.db.query(delete_query, (del_id,))

    def runner(self):
        chosen = random.choices([self.update, self.delete, self.insert], weights=(0.25, 0.05, 0.7), k=1)[0]
        chosen()
