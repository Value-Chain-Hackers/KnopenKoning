from sqlalchemy import Column, Integer, String
from .session import Base 

class Crews(Base):
    __tablename__ = 'crews'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(256), index=True)
    process = Column(String(1024), nullable=True)
    agents = Column(String(1024), nullable=True)
