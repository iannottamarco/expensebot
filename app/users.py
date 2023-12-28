# Standard library imports
import logging

# Third-party imports
from sqlalchemy.exc import SQLAlchemyError

# Local application imports
from .db_utils import Session, add_to_session_and_close
from .models import User

# Configure logging
logging.basicConfig(filename='./logs/mylogs.log',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def is_user_registered(telegram_id):
    """
    Checks whether a user is registered based on the given Telegram ID.

    Args:
        telegram_id (int): The Telegram ID of the user to check.

    Returns:
        bool: True if the user is registered, False otherwise.

    Raises:
        SQLAlchemyError: If there is a database related error.
        Exception: For any other unexpected errors.
    """
    try:
        with Session() as session:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()

            if user:
                logging.info(f'The User with telegram id: {telegram_id} is already registered.')
                return True
            else:
                logging.info(f'The User with telegram id: {telegram_id} has yet to register.')
                return False

    except SQLAlchemyError as e:
        logging.error(f'Error occurred while checking registration status for telegram id: {telegram_id}. Error: {e}')
        raise
    except Exception as e:
        logging.error(f'Unexpected error while checking registration status for telegram id: {telegram_id}. Error: {e}')
        raise


def create_user(email, telegram_id, chat_id=None, first_name=None, last_name=None):
    """
    Creates a new user and adds them to the database.

    Args:
        email (str): Email of the user.
        telegram_id (int): Telegram ID of the user.
        chat_id (int, optional): Chat ID of the user.
        first_name (str, optional): First name of the user.
        last_name (str, optional): Last name of the user.

    Returns:
        User: The newly created User object.

    Raises:
        SQLAlchemyError: If there is a database related error.
        Exception: For any other unexpected errors.
    """
    try:
        with Session() as session:
            new_user = User(telegram_id=telegram_id, chat_id=chat_id, email=email, 
                            first_name=first_name, last_name=last_name)
            session.add(new_user)
            session.commit()
            return new_user

    except SQLAlchemyError as e:
        logging.error(f'Error creating user {telegram_id}: {e}')
        raise
    except Exception as e:
        logging.error(f'Unexpected error while creating user {telegram_id}: {e}')
        raise


def delete_user(telegram_id):
    """
    Deletes a user based on the provided Telegram ID.

    Args:
        telegram_id (int): The Telegram ID of the user to be deleted.

    Returns:
        bool: True if the user was successfully deleted, False otherwise.

    Raises:
        SQLAlchemyError: If there is a database related error.
        Exception: For any other unexpected errors.
    """
    try:
        with Session() as session:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()

            if user:
                session.delete(user)
                session.commit()
                logging.info(f'User with Telegram ID {telegram_id} deleted successfully.')
                return True
            else:
                logging.warning(f'User with Telegram ID {telegram_id} not found for deletion.')
                return False

    except SQLAlchemyError as e:
        logging.error(f'Error occurred while deleting user with Telegram ID {telegram_id}: {e}')
        raise
    except Exception as e:
        logging.error(f'Unexpected error while deleting user with Telegram ID {telegram_id}: {e}')
        raise