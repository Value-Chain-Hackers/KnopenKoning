
from sqlalchemy import Column, Integer, String
from .session import Base 

class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True, index=True)
    doc_hash = Column(String(255), index=True)
    name = Column(String(255), index=True)
    file_type = Column(String(255), index=True)
    file_size = Column(Integer)
    file_path = Column(String(255), index=True)
    processed = Column(Integer)
    processed_at = Column(String(255))