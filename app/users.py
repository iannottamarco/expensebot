from .db_utils import Session, add_to_session_and_close
from .models import User

import logging

logging.basicConfig(filename='./logs/mylogs.log',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)


def is_user_registered(telegram_id):
    session = Session()
    try:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            logging.info(f'The User with telegram id: {telegram_id} is already registered.')
            return True
        else:
            logging.info(f'The User with telegram id: {telegram_id} has yet to register.')
            return False
    except Exception as e:
        logging.error(f'Error occurred while checking registration status for telegram id: {telegram_id}. Error: {e}')
        return False
    finally:
        session.close()

print(is_user_registered(17073726))


def create_user(email, telegram_id, chat_id=None, first_name=None, last_name=None):
    session = Session()
    new_user = User(telegram_id=telegram_id, chat_id=chat_id,email=email, first_name=first_name, last_name=last_name)
    try:
        add_to_session_and_close(session,new_user)
        return new_user
    except Exception as e:
        session.rollback()
        print(f'Error creating user {telegram_id}: {e}')
        raise
    finally:
        session.close()



def delete_user(telegram_id):
    session = Session()
    try:
        # Query for the user with the specified Telegram ID
        user = session.query(User).filter(User.telegram_id == telegram_id).first()

        if user:
            # User found, proceed with deletion
            session.delete(user)
            session.commit()
            logging.info(f'User with Telegram ID {telegram_id} deleted successfully.')
        else:
            # User not found
            logging.warning(f'User with Telegram ID {telegram_id} not found for deletion.')
            return False  # Or handle it differently based on your application logic

        return True
    except Exception as e:
        session.rollback()
        logging.error(f'Error occurred while deleting user with Telegram ID {telegram_id}: {e}')
        return False
    finally:
        session.close()