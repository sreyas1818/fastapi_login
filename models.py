from sqlalchemy import Column, Integer, String, Text, ForeignKey,Boolean


from database import Base

class Donor(Base):
    __tablename__ = "donors"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    blood_group = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    city = Column(String, nullable=False)
    availability = Column(Boolean, default=True)







class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
from sqlalchemy import Column, Integer, String, Text

class BloodRequest(Base):
    __tablename__ = "blood_requests"

    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String, nullable=False)
    blood_group = Column(String, nullable=False)
    units = Column(Integer, nullable=False)
    hospital = Column(String, nullable=False)
    city = Column(String, nullable=False)
    contact = Column(String, nullable=False)
    notes = Column(Text)

    status = Column(String, default="Pending")
