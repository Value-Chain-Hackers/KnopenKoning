from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker

from db import Base, engine
from db import Company, Records


def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully!")
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    # Test database connection
    try:
        connection = engine.connect()
        print("Connected to the database!")
        connection.close()
    except Exception as e:
        print(f"Error occurred: {e}")
    
    # Create tables
    create_tables()