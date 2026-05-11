from sqlalchemy import Column, Integer, String, DateTime, Boolean, func, Float
from app.db.db_config import Base
from datetime import datetime
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)

    level = Column(String, default="A1")
    xp = Column(Integer, default=0)

    is_admin = Column(Boolean, default=False)

    created_at = Column(DateTime, default=func.now())

    # relationships
    # words = relationship("UserWord", back_populates="user")
    # tests = relationship("TestResult", back_populates="user")