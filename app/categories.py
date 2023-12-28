# Standard library imports
import logging

# Third-party imports
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

# Local application imports
from .db_utils import Session, add_to_session_and_close
from .models import Category

# Configure logging
logging.basicConfig(filename='./logs/mylogs.log',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def add_category(user_id, name, description=None):
    """
    Adds a new category for a user. If the category already exists or the user has reached
    the maximum number of categories, the function raises an exception.

    Args:
        user_id (int): The user's ID.
        name (str): The name of the category.
        description (str, optional): Optional description of the category.

    Returns:
        Category: The new Category object if added successfully.

    Raises:
        ValueError: If the maximum number of categories is reached or the category already exists.
        SQLAlchemyError: If there is a database related error.
        Exception: For any other unexpected errors.
    """
    try: 
        with Session() as session:
            if count_active_categories(user_id) >= 20:
                logging.error(f'User {user_id} has reached the maximum number of categories (20).')
                raise ValueError('Maximum number of categories reached')

            existing_category = session.query(Category)\
                                    .filter(Category.user_id == user_id, 
                                            func.lower(Category.name) == func.lower(name))\
                                    .first()

            if existing_category:
                logging.error(f'Category named {name} already exists for user {user_id}')
                raise ValueError('This category already exists')

            new_category = Category(user_id=user_id, name=name, description=description)
            add_to_session_and_close(session, new_category)
            logging.info(f'Category added by user:{user_id} {name}')
            return True
    
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f'DB error creating category for user:{user_id}: {e}')
        raise

    except Exception as e:
        session.rollback()
        logging.error(f'Unexpected error adding category for user:{user_id}: {e}')
        raise

    finally:
        session.close()


def delete_category(user_id, name):
    """
    Deletes a category for a user based on the category name.

    Args:
        user_id (int): The user's ID.
        name (str): The name of the category to be deleted.

    Returns:
        str: A message indicating the result of the delete operation.

    Raises:
        SQLAlchemyError: If there is a database related error.
        Exception: For any other unexpected errors.
    """
    try:
        with Session() as session:
            category = session.query(Category)\
                            .filter(Category.user_id == user_id, func.lower(Category.name) == func.lower(name))\
                            .first()

            if category:
                session.delete(category)
                session.commit()
                logging.info(f'Category {name} deleted for user {user_id}.')
                return 'Category deleted successfully'
            else:
                logging.error(f'Category {name} not found for user {user_id}.')
                return 'Category not found'

    except SQLAlchemyError as e:
        logging.error(f'DB error deleting category {name} for user {user_id}: {e}')
        raise
    except Exception as e:
        logging.error(f'Unexpected error deleting category for user {user_id}: {e}')
        raise
    finally:
        session.close()


def change_category_status(user_id, category_id, activate):
    """
    Changes the activation status of a specific category for a user.

    Args:
        user_id (int): The user's ID.
        category_id (int): The ID of the category to be updated.
        activate (bool): True to activate the category, False to deactivate.

    Returns:
        bool: True if the category status was successfully changed, False otherwise.

    Raises:
        SQLAlchemyError: If there is a database related error.
        Exception: For any other unexpected errors.
    """
    try:
        with Session() as session:
            category = session.query(Category)\
                            .filter(Category.user_id == user_id, 
                                    Category.id == category_id)\
                            .first()

            if category:
                category.active = activate
                session.commit()

                action = "reactivated" if activate else "deactivated"
                logging.info(f'Category {category_id} {action} for user {user_id}.')
                return True
            else:
                logging.error(f'Category {category_id} not found for user {user_id}.')
                return False

    except SQLAlchemyError as e:
        logging.error(f'DB error changing status of category {category_id} for user {user_id}: {e}')
        raise
    except Exception as e:
        logging.error(f'Unexpected error changing category status for user {user_id}: {e}')
        raise


def count_active_categories(user_id):
    """
    Counts the number of active categories for a given user.

    Args:
        user_id (int): The user's ID for whom the active categories are counted.

    Returns:
        int: The number of active categories for the user.

    Raises:
        SQLAlchemyError: If there is a database related error.
        Exception: For any other unexpected errors.
    """
    try:
        with Session() as session:
            active_category_count = session.query(Category)\
                                           .filter(Category.user_id == user_id, Category.active == True)\
                                           .count()

            logging.info(f'User {user_id} has {active_category_count} active categories.')
            return active_category_count

    except SQLAlchemyError as e:
        logging.error(f'Error counting active categories for user {user_id}: {e}')
        raise
    except Exception as e:
        logging.error(f'Unexpected error while counting active categories for user {user_id}: {e}')
        raise


def get_categories(user_id, type=0):
    """
    Fetches categories based on the specified type for a given user.

    Args:
        user_id (int): The user's ID for whom the categories are fetched.
        type (int): Determines the type of categories to fetch. 
                    0 for both active and inactive, 
                    1 for only active, 
                    2 for only inactive.

    Returns:
        list: A list of category names based on the specified type.

    Raises:
        SQLAlchemyError: If there is a database related error.
        Exception: For any other unexpected errors.
    """
    try:
        with Session() as session:
            query = session.query(Category.name).filter(Category.user_id == user_id)
            
            if type == 1:
                query = query.filter(Category.active == True)
            elif type == 2:
                query = query.filter(Category.active == False)

            categories_tuples = query.all()
            categories = [category[0] for category in categories_tuples]

            logging.info(f'Categories retrieved for user {user_id}.')
            return categories

    except SQLAlchemyError as e:
        logging.error(f'Error retrieving categories for user {user_id}: {e}')
        raise
    except Exception as e:
        logging.error(f'Unexpected error while retrieving categories for user {user_id}: {e}')
        raise


def get_categories_and_id(user_id, type=0):
    """
    Fetches categories along with their IDs based on the specified type for a given user.

    Args:
        user_id (int): The user's ID for whom the categories are fetched.
        type (int): Determines the type of categories to fetch. 
                    0 for both active and inactive, 
                    1 for only active, 
                    2 for only inactive.

    Returns:
        list: A list of tuples, each containing the category name and ID, based on the specified type.

    Raises:
        SQLAlchemyError: If there is a database related error.
        Exception: For any other unexpected errors.
    """
    try:
        with Session() as session:
            query = session.query(Category.name, Category.id).filter(Category.user_id == user_id)
            
            if type == 1: 
                query = query.filter(Category.active == True)
            elif type == 2:
                query = query.filter(Category.active == False)

            categories_tuples = query.all()
            categories = [[category.name, category.id] for category in categories_tuples]

            logging.info(f'Categories retrieved for user {user_id}.')
            return categories

    except SQLAlchemyError as e:
        logging.error(f'Error retrieving categories for user {user_id}: {e}')
        raise
    except Exception as e:
        logging.error(f'Unexpected error while retrieving categories for user {user_id}: {e}')
        raise


def generate_categories_message(user_id, type=0):
    """
    Generates a message listing active and/or inactive categories for a given user.

    Args:
        user_id (int): The user's ID for whom the categories are listed.
        type (int): Determines the type of categories to list. 
                    0 for both active and inactive, 
                    1 for only active, 
                    2 for only inactive.

    Returns:
        str: A formatted message listing the requested categories.

    Raises:
        Exception: For any unexpected errors during the process.
    """
    try:
        message = ""

        if type in [0, 1]:  # Generate list of active categories
            active_categories = get_categories(user_id, type=1)
            if active_categories:
                message += "Active categories:\n" + "\n".join(active_categories) + "\n\n"

        if type in [0, 2]:  # Generate list of inactive categories
            inactive_categories = get_categories(user_id, type=2)
            if inactive_categories:
                message += "Deactivated categories:\n" + "\n".join(inactive_categories)

        if not message:
            message = "No categories found."

        return message

    except Exception as e:
        logging.error(f'Error generating categories message for user {user_id}: {e}')
        return "An error occurred while retrieving categories."


def get_category_name(user_id, category_id):
    """
    Retrieves the name of a specific category for a given user based on the category ID.

    Args:
        user_id (int): The user's ID.
        category_id (int): The ID of the category.

    Returns:
        str: The name of the category, or an error message if retrieval fails.

    Raises:
        SQLAlchemyError: If there is a database related error.
        Exception: For any other unexpected errors.
    """
    try:
        with Session() as session:
            category = session.query(Category)\
                              .filter(Category.user_id == user_id, 
                                      Category.id == category_id)\
                              .first()

            if category is not None:
                return category.name
            else:
                return "Category not found"

    except SQLAlchemyError as e:
        logging.error(f'Error retrieving user category for {user_id} and category_id {category_id}: {e}')
        raise
    except Exception as e:
        logging.error(f'Unexpected error while retrieving category for {user_id} and category_id {category_id}: {e}')
        raise