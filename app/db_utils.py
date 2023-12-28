# Standard library imports
import os
import logging

# Third-party imports
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(filename='./logs/mylogs.log',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

# SSL arguments for database connection
ssl_args = {
    'ssl': {
        'ca': './Misc/cacert.pem'
    }
}


def get_db_uri():
    """
    Constructs and returns the database URI for the MySQL database connection.

    Returns:
        str: The constructed database URI.
    """
    database_type = 'mysql'
    db_driver = 'pymysql'
    username = os.getenv('DATABASE_USERNAME')
    password = os.getenv('DATABASE_PASSWORD')
    database_name = 'expensebot'
    database_host = os.getenv('DATABASE_HOST')
    database_port = '3306'

    # Constructing the connection string
    return f'{database_type}+{db_driver}://{username}:{password}@{database_host}:{database_port}/{database_name}'



# Creating the engine
db_uri = get_db_uri()
engine = create_engine(db_uri, connect_args=ssl_args)
# Create the Session
Session = sessionmaker(bind=engine)


def add_to_session_and_close(session, obj):
    """
    Adds an object to the given SQLAlchemy session and commits the session.

    Args:
        session (Session): The SQLAlchemy session to which the object is added.
        obj (object): The object to be added to the session.

    Raises:
        SQLAlchemyError: If there is an error during the database operation.
    """
    try:
        session.add(obj)
        session.commit()
        logging.info(f'Object of type {type(obj).__name__} added successfully.')
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f'Error adding object of type {type(obj).__name__}: {e}')
        raise  # Reraising the exception to be handled by the caller
    except Exception as e:
        # Catching any other exceptions that are not related to SQLAlchemy
        logging.error(f'Unexpected error: {e}')
        raise
    finally:
        session.close()
        logging.debug('Session closed.')


def confirm_operation(telegram_user_id, userprovided_id):
    """
    Confirms whether the provided user ID matches the Telegram user's ID.

    Args:
        telegram_user_id (int): The Telegram user's ID.
        userprovided_id (int): The user-provided ID to be confirmed.

    Returns:
        bool: True if the IDs match, False otherwise.
    """
    if telegram_user_id == userprovided_id:
        logging.info(f'User {telegram_user_id} has confirmed the operation')
        return True
    else:
        logging.warning(f'User {telegram_user_id} failed confirming the operation')
        return False
