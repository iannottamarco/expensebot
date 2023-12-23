from sqlalchemy import func
from .db_utils import Session, add_to_session_and_close
from .models import Category

import logging
logging.basicConfig(filename='./logs/mylogs.log',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)


def add_category(user_id, name, description=None):
    session = Session()
    try:
        category_count = count_active_categories(user_id)
        
        if category_count >= 15:
            logging.error(f'User {user_id} has reached the maximum number of categories (15).')
            return 'Maximum number of categories reached'

        existing_category = session.query(Category)\
                                   .filter(Category.user_id == user_id, 
                                           func.lower(Category.name) == func.lower(name))\
                                   .first()

        if existing_category is None:
            new_category = Category(user_id=user_id, name=name, description=description)
            add_to_session_and_close(session, new_category)
            logging.info(f'Category added by user:{user_id} : {name}')
            return new_category
        else:
            logging.error(f'Category named {name} already exists for user {user_id}')
            return 'This Category already exists'
    except Exception as e:
        session.rollback()
        logging.error(f'Error adding category for user:{user_id}: {e}')
        return None
    finally:
        session.close()


def delete_category(user_id, name):
    session = Session()
    try:
        category = session.query(Category)\
                          .filter(Category.user_id == user_id, func.lower(Category.name) == func.lower(name))\
                          .first()

        if category:
            session.delete(category)
            session.commit()
            logging.info(f'Category {name} deleted for user {user_id}.')
        else:
            logging.warning(f'Category {name} not found for user {user_id}.')
            return 'Category not found'

        return 'Category deleted successfully'
    except Exception as e:
        session.rollback()
        logging.error(f'Error deleting category {name} for user {user_id}: {e}')
        return 'Error deleting category'
    finally:
        session.close()


def change_category_status(user_id, category_id, activate):
    session = Session()
    try:

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
            logging.warning(f'Category {category_id} not found for user {user_id}.')
            return False
    except Exception as e:
        session.rollback()
        logging.error(f'Error changing status of category {category_id} for user {user_id}: {e}')
        return f'Error changing status of category'
    finally:
        session.close()

def count_active_categories(user_id):
    session = Session()
    try:
        active_category_count = session.query(Category)\
                                       .filter(Category.user_id == user_id, Category.active == True)\
                                       .count()

        logging.info(f'User {user_id} has {active_category_count} active categories.')
        return active_category_count 
    except Exception as e:
        logging.error(f'Error counting active categories for user {user_id}: {e}')
        return 0 
    finally:
        session.close()

def get_categories(user_id, type=0):
    '''
    Type = 0: Fetch both active and inactive categories
    Type = 1: Fetch only active categories
    Type = 2: Fetch only inactive categories
    '''
    session = Session()
    try:
        query = session.query(Category.name).filter(Category.user_id == user_id)
        
        if type == 1:
            query = query.filter(Category.active == True)
        elif type == 2:
            query = query.filter(Category.active == False)
        # If type == 0, no additional filter is applied

        categories_tuples = query.all()
        categories = [category[0] for category in categories_tuples]

        logging.info(f'Categories retrieved for user {user_id}.')
        return categories
    except Exception as e:
        logging.error(f'Error retrieving categories for user {user_id}: {e}')
        return None
    finally:
        session.close()

def get_categories_and_id(user_id, type=0):
    '''
    Type = 0: Fetch both active and inactive categories
    Type = 1: Fetch only active categories
    Type = 2: Fetch only inactive categories
    '''
    session = Session()
    try:
        query = session.query(Category.name, Category.id).filter(Category.user_id == user_id)
        
        if type == 1:  # Only active categories
            query = query.filter(Category.active == True)
        elif type == 2:  # Only inactive categories
            query = query.filter(Category.active == False)
        # If type == 0, no additional filter is applied

        categories_tuples = query.all()
        categories = [[category.name, category.id] for category in categories_tuples]

        logging.info(f'Categories retrieved for user {user_id}.')
        return categories
    except Exception as e:
        logging.error(f'Error retrieving categories for user {user_id}: {e}')
        return None
    finally:
        session.close()


def generate_categories_message(user_id, type=0):
    '''
    Type = 0 Generate list of both active and inactive categories
    Type = 1 Generate list of active categories
    Type = 2 Generate list of inactive categories
    '''
    try:
        message = ""

        if type in [0, 1]:
            active_categories = get_categories(user_id, type=1)
            if active_categories:
                message += "Active categories:\n" + "\n".join(active_categories) + "\n\n"

        if type in [0, 2]:
            inactive_categories = get_categories(user_id, type=2)
            if inactive_categories:
                message += "Deactivated categories:\n" + "\n".join(inactive_categories)

        if not message:
            message = "No categories found."

        return message
    except Exception as e:
        logging.error(f'Error generating categories message for user {user_id}: {e}')
        return "An error occurred while retrieving categories."


def get_category_name(user_id,category_id):
    session = Session()

    try:
        category_name = session.query(Category)\
                                   .filter(Category.user_id == user_id, 
                                           Category.id == category_id)\
                                   .first()
        return category_name.name
    
    except Exception as e:
        logging.error(f'Error retrieving user category for {user_id} and category_id {category_id}: {e}')
        return "An error occurred while retrieving category"