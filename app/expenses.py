from .db_utils import Session, add_to_session_and_close
from .models import Expense, Category

import logging
logging.basicConfig(filename='./logs/mylogs.log',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)


def add_expense(amount, category_id, user_id,date):
    session = Session()
    date = str(date)
    try:
        new_expense = Expense(amount=amount, category_id=category_id, user_id=user_id,date=date)
        add_to_session_and_close(session,new_expense)
        logging.info(f'Expense added by user:{user_id} : {amount}')
        return new_expense
    except Exception as e:
        session.rollback()
        logging.error(f'Error adding expense of user:{user_id}: {e}')
        return None
    finally:
        session.close()

def delete_expense(user_id,expense_id):
    session = Session() 

    try:
        expense = session.query(Expense).filter_by(user_id=user_id, id=expense_id).first()

        if expense:
            session.delete(expense)
            session.commit()
            return "Expense deleted successfully."
        else:
            
            return "Expense not found or does not belong to the user."

    except Exception as e:
        session.rollback()  # Rollback the session in case of an error
        return f"An error occurred: {e}"

    finally:
        session.close()  # Close the session
    

def retrieve_last5_expenses(user_id):
    session = Session()
    try:
        # Perform the query with a join and select specific fields
        expenses = session.query(Expense.id, Expense.amount, Category.name)\
                          .join(Category, Expense.category_id == Category.id)\
                          .filter(Expense.user_id == user_id)\
                          .order_by(Expense.created_at.desc())\
                          .limit(5)\
                          .all()
        logging.info(f'{user_id} expenses retrieved.')
        return expenses
    except Exception as e:
        session.rollback()
        logging.error(f'Error retrieving last 5 expenses of user:{user_id}: {e}')
        return None
    finally:
        session.close()

