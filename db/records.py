from sqlalchemy import Column, Integer, String
from .session import Base 

class Records(Base):
    __tablename__ = 'records'
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, index=True)
    record_type = Column(String(100), index=True)
    record_name = Column(String(255), index=True)
    record_path = Column(String(1024))
