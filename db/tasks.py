from sqlalchemy import Column, Integer, String
from .session import Base 

class Tasks(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    expected_output = Column(String)
    tools = Column(String, default="")
    asynchronious = Column(Integer, default=0)
    context = Column(String)
    config = Column(String)
    output_json = Column(String)
    output_pydantic = Column(String)
    output_file = Column(String)
    human_input = Column(Integer)