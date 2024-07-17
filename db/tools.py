from sqlalchemy import Column, Integer, String
from .session import Base 

class Tools(Base):
    __tablename__ = 'tools'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(256))
    description = Column(String(1024))
    output = Column(String(1024), default="")
    enabled = Column(Integer, default=1)
