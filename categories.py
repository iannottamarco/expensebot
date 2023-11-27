from sqlalchemy import func
from db_utils import Session
from db_utils import add_to_session_and_close
from models import Category

import logging
logging.basicConfig(filename='mylogs.log',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)


def add_category(user_id, name, description=None):
    session = Session()
    try:
        category_count = count_active_categories(user_id)
        
        if category_count >= 10:
            logging.error(f'User {user_id} has reached the maximum number of categories (10).')
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


def deactivate_category(user_id, name):
    session = Session()
    try:
        category = session.query(Category)\
                          .filter(Category.user_id == user_id, 
                                  func.lower(Category.name) == func.lower(name))\
                          .first()

        if category:
            category.active = False
            session.commit()
            logging.info(f'Category {name} deactivated for user {user_id}.')
            return 'Category deactivated successfully'
        else:
            logging.warning(f'Category {name} not found for user {user_id}.')
            return 'Category not found'
    except Exception as e:
        session.rollback()
        logging.error(f'Error deactivating category {name} for user {user_id}: {e}')
        return 'Error deactivating category'
    finally:
        session.close()


def reactivate_category(user_id, name):
    session = Session()
    try:
        category = session.query(Category)\
                          .filter(Category.user_id == user_id, 
                                  func.lower(Category.name) == func.lower(name))\
                          .first()

        if category:
            category.active = True
            session.commit()
            logging.info(f'Category {name} reactivated for user {user_id}.')
            return 'Category reactivated successfully'
        else:
            logging.warning(f'Category {name} not found for user {user_id}.')
            return 'Category not found'
    except Exception as e:
        session.rollback()
        logging.error(f'Error reactivating category {name} for user {user_id}: {e}')
        return 'Error reactivating category'
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