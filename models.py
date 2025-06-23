from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base

class Contact(Base):
    __tablename__ = "contact"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String)
    phone = Column(String)
    linkedin = Column(String)
    address = Column(String)

class AnalyseCandidat(Base):
    __tablename__ = "analyse_candidat"
    id = Column(Integer, primary_key=True, index=True)
    analyse = Column(String)

class ProfileCandidat(Base):
    __tablename__ = "profile_candidat"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    title = Column(String)
    profile = Column(String)
    contact_id = Column(Integer, ForeignKey("contact.id"))
    analyse_id = Column(Integer, ForeignKey("analyse_candidat.id"))
    education = Column(JSON)
    languages = Column(JSON)
    certificates = Column(JSON)
    skills = Column(JSON)

    contact = relationship("Contact")
    analyse = relationship("AnalyseCandidat")
