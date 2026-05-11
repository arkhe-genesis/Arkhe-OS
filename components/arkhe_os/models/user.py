from sqlalchemy import Column, Integer, String, Boolean, Enum
import enum
from arkhe_os.db.session import Base

class UserRole(str, enum.Enum):
    ARCHITECT = "architect"
    OBSERVER = "observer"
    OPERATOR = "operator"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean(), default=True)
    role = Column(String, default=UserRole.OBSERVER)
