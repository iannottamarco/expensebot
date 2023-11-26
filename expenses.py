from db_utils import Session
from db_utils import add_to_session_and_close
from models import Expense

import logging
logging.basicConfig(filename='mylogs.log',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)


def add_expense(amount, category_id, user_id):
    session = Session()
    print('session',session)
    try:
        new_expense = Expense(amount=amount, category_id=category_id, user_id=user_id)
        add_to_session_and_close(session,new_expense)
        logging.info(f'Expense added by user:{user_id} : {amount}')
        return new_expense
    except Exception as e:
        session.rollback()
        logging.error(f'Error adding expense of user:{user_id}: {e}')
        return None
    finally:
        session.close()