from sqlalchemy import Column, Integer, String
from .session import Base 

class Tasks(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String(255))
    expected_output = Column(String(1024))
    tools = Column(String(1024), default="")
    asynchronious = Column(Integer, default=0)
    context = Column(String(1024))
    config = Column(String(512))
    output_json = Column(String(512))
    output_pydantic = Column(String(512))
    output_file = Column(String(512))
    human_input = Column(Integer)