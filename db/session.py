from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
MYSQL_DATABASE_URL = os.getenv("MYSQL_DATABASE_URL",  "mysql+mysqlconnector://vch_user:rQMK5oLIg5i7KBiyk7uhy7uQqVg3cyjx@mysql/vch")

engine = create_engine(MYSQL_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()