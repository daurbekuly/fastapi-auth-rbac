from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False) # Admin, Manager, User

    users = relationship("User", back_populates="role")
    rules = relationship("AccessRule", back_populates="role")

class BusinessElement(Base):
    __tablename__ = "business_elements"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False) # "users", "goods", "orders"

class AccessRule(Base):
    __tablename__ = "access_rules"
    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    element_id = Column(Integer, ForeignKey("business_elements.id"))
    
    can_create = Column(Boolean, default=False)
    can_read = Column(Boolean, default=False)
    can_read_all = Column(Boolean, default=False)
    can_update = Column(Boolean, default=False)
    can_update_all = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_delete_all = Column(Boolean, default=False)

    role = relationship("Role", back_populates="rules")