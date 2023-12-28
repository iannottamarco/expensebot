import logging

# Configure logging
logging.basicConfig(filename='./logs/mylogs.log',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

# Import local modules
from .db_utils import Session, add_to_session_and_close
from .models import Expense, Category


def add_expense(amount, category_id, user_id, description, date):
    """
    Adds a new expense to the database.

    Args:
        amount (str): The amount of the expense, can include commas as decimal separators.
        category_id (int): The ID of the category for this expense.
        user_id (int): The ID of the user who is adding the expense.
        description (str): A brief description of the expense.
        date (str): The date of the expense.

    Returns:
        Expense: The newly created expense object or None in case of an error.
    """
    try:
        with Session() as session:
            # Normalize amount by replacing commas with dots and converting to float
            normalized_amount = float(str(amount).replace(',', '.'))
            new_expense = Expense(amount=normalized_amount, category_id=category_id, 
                                user_id=user_id, description=description, date=date)
            add_to_session_and_close(session, new_expense)
            logging.info(f'Expense added for user {user_id}: {normalized_amount}')
            return True
    except Exception as e:
        session.rollback()
        logging.error(f'Error adding expense for user {user_id}: {e}')
        return None



def delete_expense(user_id, expense_id):
    """
    Deletes an expense from the database.

    Args:
        user_id (int): The ID of the user who owns the expense.
        expense_id (int): The ID of the expense to be deleted.

    Returns:
        bool: True if the expense was successfully deleted, False otherwise.
    """
    try:
        with Session() as session:
            expense = session.query(Expense).filter_by(user_id=user_id, id=expense_id).first()

            if expense:
                session.delete(expense)
                session.commit()
                logging.info(f"Expense {expense_id} successfully deleted for user {user_id}.")
                return True
            else:
                # If no expense is found, return False instead of None for clarity
                logging.info(f"No expense found with ID {expense_id} for user {user_id}.")
                return False

    except Exception as e:
        session.rollback()
        logging.error(f"Error deleting expense {expense_id} for user {user_id}: {e}")
        return False
    

def retrieve_last5_expenses(user_id):
    """
    Retrieves the last five expenses for a given user.

    Args:
        user_id (int): The ID of the user whose expenses are to be retrieved.

    Returns:
        list: A list of the last five expenses, each as a tuple (id, amount, category name),
              or None if an error occurs.
    """
    try:
        with Session() as session:
            expenses = session.query(Expense.id, Expense.amount, Category.name)\
                            .join(Category, Expense.category_id == Category.id)\
                            .filter(Expense.user_id == user_id)\
                            .order_by(Expense.created_at.desc())\
                            .limit(5)\
                            .all()
            logging.info(f"Last 5 expenses retrieved for user {user_id}.")
            return expenses

    except Exception as e:
        session.rollback()
        logging.error(f"Error retrieving last 5 expenses for user {user_id}: {e}")
        return None


def retrieve_last_expense_id(user_id):
    """
    Retrieves the ID of the most recent expense for a specific user.

    Args:
        user_id (int): The ID of the user.

    Returns:
        int or None: The ID of the most recent expense if found, otherwise None.
    """
    try:
        with Session() as session:
            expense_record = session.query(Expense.id)\
                                    .filter(Expense.user_id == user_id)\
                                    .order_by(Expense.created_at.desc())\
                                    .first()
            if expense_record:
                logging.info(f"Last expense ID retrieved for user {user_id}.")
                return expense_record[0]  # Directly return the ID
            else:
                logging.info(f"No expenses found for user {user_id}.")
                return None

    except Exception as e:
        session.rollback()
        logging.error(f"Error retrieving last expense for user {user_id}: {e}")
        return None