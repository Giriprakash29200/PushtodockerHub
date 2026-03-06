from sqlalchemy import Column, Integer, String
from database import Base

class Student(Base):
    __tablename__ = "students"

    register_number = Column(String, primary_key=True, index=True)   # manually entered register number
    name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    password = Column(String, nullable=False)