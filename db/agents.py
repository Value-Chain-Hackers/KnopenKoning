from sqlalchemy import Column, Integer, String
from .session import Base 

class Agents(Base):
    __tablename__ = 'agents'
    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(256), index=True)
    goal = Column(String(1024))
    backstory = Column(String(4096))
    tools = Column(String(4096))
    llm = Column(String(256))
    llm_functions = Column(String(256))
    max_iter = Column(Integer, default=25)
    max_rpm = Column(Integer, nullable=True, default=None)
    max_time = Column(Integer, nullable=True)
    verbose = Column(Integer, default=0)
    allow_delegation = Column(Integer, default=0)
    cache = Column(Integer, default=1)
