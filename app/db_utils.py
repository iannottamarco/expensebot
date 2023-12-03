from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(filename='./logs/mylogs.log',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)


## DATABASE SETUP
def get_db_uri():
    DATABASE_TYPE = 'mysql'
    DB_DRIVER = 'pymysql'
    USERNAME = os.getenv('DATABASE_USERNAME')
    PASSWORD = os.getenv('DATABASE_PASSWORD')
    DATABASE_NAME = 'expensebot'
    DATABASE_HOST = os.getenv('DATABASE_HOST')
    DATABASE_PORT = '3306'

    # Constructing the connection string
    DATABASE_URI = f'{DATABASE_TYPE}+{DB_DRIVER}://{USERNAME}:{PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}'
    return DATABASE_URI

ssl_args = {
    'ssl': {
        'ca': './Misc/cacert.pem'
    }
}

# Creating the engine
engine = create_engine(get_db_uri(), connect_args=ssl_args)

Session = sessionmaker(bind=engine)


def add_to_session_and_close(session, obj):
    try:
        session.add(obj)
        session.commit()
        logging.info(f'Object of type {type(obj).__name__} added successfully.')
    except Exception as e:
        session.rollback()
        logging.error(f'Error adding object: {e}')
        raise  # Re-raise the exception if you want calling code to handle it as well
    finally:
        session.close()
        logging.info('Session closed.')


def add_and_commit(session, obj):
    try:
        session.add(obj)
        session.commit()
        logging.info(f'Object {obj} added and committed successfully.')
    except Exception as e:
        session.rollback()
        logging.error(f'Error during add and commit: {e}')
        raise  # Re-raise the exception for the calling code to handle


def confirm_operation(telegram_user_id,userprovided_id):
    if telegram_user_id == userprovided_id:
        logging.info(f'{telegram_user_id} has confirmed the operation')
        return True
    else:
        logging.info(f'{telegram_user_id} failed confirming the operation')
        return False