import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

db_host = os.getenv('DATABASE_HOST')
db_username = os.getenv('DATABASE_USERNAME')
db_password = os.getenv('DATABASE_PASSWORD')
db_dbname = 'expensebot'


def connect_to_db():
    return mysql.connector.connect(
        host= db_host,
        user=db_username,
        password=db_password,
        database=db_dbname
    )

def is_user_registered(user_id):
    db = connect_to_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        return user is not None
    finally:
        cursor.close()
        db.close()

def register_user(user_id, name, surname):
    db = connect_to_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO users (id, name, surname) VALUES (%s, %s, %s)",
                       (user_id, name, surname))
        db.commit()
    finally:
        cursor.close()
        db.close()