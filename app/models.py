# Standard library imports
from datetime import datetime
import logging

# Third-party imports
from sqlalchemy import  Column, Integer, String, DateTime, Float, Boolean
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import SQLAlchemyError

# Local application imports
from .db_utils import get_db_uri, engine

# Configure logging
logging.basicConfig(filename='./logs/mylogs.log',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)


## CREATE TABLES
Base = declarative_base()

## USERS
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    first_name = Column(String(20), nullable=True)
    last_name = Column(String(20), nullable=True)
    email = Column(String(50), unique=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    chat_id = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


## CATEGORIES
class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(300))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


## EXPENSES
class Expense(Base):
    __tablename__ = 'expenses'

    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    user_id = Column(Integer, nullable=False)
    category_id = Column(Integer, nullable=False)
    description = Column(String(300))
    date = Column(DateTime,default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

## GSHEET
class UserGoogleSheetsCredentials(Base):
    __tablename__ = 'gsheet'

    user_id = Column(Integer, primary_key=True)
    access_token = Column(String(255))
    refresh_token = Column(String(255))
    token_expiry = Column(DateTime)
    spreadsheet_id = Column(String(255))
    sheet_name = Column(String(30))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

if __name__ == '__main__':
    print("Creating tables...")
    Base.metadata.create_all(engine)
    print("Tables created successfully.")
    print("Execute: ALTER TABLE users AUTO_INCREMENT = 10000 on database console")