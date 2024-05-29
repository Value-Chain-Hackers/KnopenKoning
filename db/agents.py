from sqlalchemy import Column, Integer, String
from .session import Base 

class Agents(Base):
    __tablename__ = 'agents'
    id = Column(Integer, primary_key=True, index=True)
    role = Column(String, index=True)
    goal = Column(String)
    backstory = Column(String)
    tools = Column(String)
    llm = Column(String)
    llm_functions = Column(String)
    max_iter = Column(Integer, default=25)
    max_rpm = Column(Integer, nullable=True, default=None)
    max_time = Column(Integer, nullable=True)
    verbose = Column(Integer, default=0)
    allow_delegation = Column(Integer, default=0)
    cache = Column(Integer, default=1)
