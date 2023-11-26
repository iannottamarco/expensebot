from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float
from sqlalchemy import create_engine
from sqlalchemy.orm import relationship, declarative_base
from db_utils import get_db_uri, engine
from datetime import datetime

import logging
logging.basicConfig(filename='mylogs.log',
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

    # PLANETSCALE DOES NOT SUPPORT FOREIGN KEY CONSTRAINTS
    # categories = relationship("Category",
    #                           back_populates="user",
    #                           viewonly=True)
    # expenses = relationship("Expense",
    #                         primaryjoin="remote(Expense.user_id) == foreign(User.id)",
    #                         back_populates="user",
    #                         viewonly=True)


## CATEGORIES
class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(300))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # PLANETSCALE DOES NOT SUPPORT FOREIGN KEY CONSTRAINTS
    # user = relationship("User",
    #                     back_populates="categories",
    #                     primaryjoin="Category.user_id == foreign(User.id)",
    #                     viewonly=True)

## EXPENSES
class Expense(Base):
    __tablename__ = 'expenses'

    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    user_id = Column(Integer, nullable=False)
    category_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # PLANETSCALE DOES NOT SUPPORT FOREIGN KEY CONSTRAINTS
    # user = relationship("User",
    #                     primaryjoin="remote(User.id) == foreign(Expense.user_id)",
    #                     back_populates="expenses",
    #                     viewonly=True)
    # category = relationship("Category",
    #                         primaryjoin="remote(Category.id) == foreign(Expense.category_id)",
    #                         back_populates="expenses",
    #                         viewonly=True)


if __name__ == '__main__':
    print("Creating tables...")
    #Base.metadata.create_all(engine)
    print("Tables created successfully.")

Expense(amount=12,user_id=123,category_id=1)