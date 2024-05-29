from sqlalchemy import Column, Integer, String
from .session import Base 

class Website(Base):
    __tablename__ = 'websites'
    url             = Column(String, primary_key=True, index=True)
    company_id      = Column(Integer, index=True)
    allowed_domains = Column(String, index=True)
    spider_class    = Column(String, index=True)
    follow_links    = Column(String, index=True)
    parse_item      = Column(String, index=True)
