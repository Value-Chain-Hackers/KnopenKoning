from sqlalchemy import Column, Integer, String
from .session import Base 

class Tools(Base):
    __tablename__ = 'tools'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    output = Column(String, default="")
    enabled = Column(Integer, default=1)
