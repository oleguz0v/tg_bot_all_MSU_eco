from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Lecture(Base):
    __tablename__ = "lectures"
    id             = Column(Integer, primary_key=True, index=True)
    direction      = Column(String, index=True)
    course         = Column(Integer, index=True)
    subject        = Column(String, index=True)
    material_type  = Column(String, index=True)
    date           = Column(Date, index=True)
    channel_msg_id = Column(Integer, index=True)
    file_id        = Column(String, nullable=False)