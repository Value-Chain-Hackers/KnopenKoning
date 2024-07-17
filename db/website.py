from sqlalchemy import Column, Integer, String
from .session import Base 

class Website(Base):
    __tablename__ = 'websites'
    url             = Column(String(512), primary_key=True, index=True)
    company_id      = Column(Integer, index=True)
    allowed_domains = Column(String(1024))
    spider_class    = Column(String(1024))
    follow_links    = Column(String(5))
    parse_item      = Column(String(255))
