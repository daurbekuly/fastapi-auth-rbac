from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from app.models.base import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users" 

    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    role = relationship("Role", back_populates="users")