import datetime
import uuid
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from typing import List, Optional

from models import RFQStatus, FileType, VendorType, EmailStatus

db = SQLAlchemy()

# Database models
class UploadedFile(db.Model):
    __tablename__ = 'uploaded_files'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    file_type = Column(SQLEnum(FileType), nullable=False)
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)
    file_path = Column(String(255), nullable=False)
    rfq_id = Column(String(36), ForeignKey('rfqs.id'), nullable=False)
    
    rfq = relationship("RFQ", back_populates="files")

class ItemDetail(db.Model):
    __tablename__ = 'item_details'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=True)    
    description = Column(Text, nullable=True)
    rfq_id = Column(String(36), ForeignKey('rfqs.id'), nullable=False)
    
    rfq = relationship("RFQ", back_populates="items")

class RFQ(db.Model):
    __tablename__ = 'rfqs'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rfq_number = Column(String(20), nullable=False, unique=True)
    client_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    status = Column(SQLEnum(RFQStatus), default=RFQStatus.DRAFT)
    notes = Column(Text, nullable=True)
    
    files = relationship("UploadedFile", back_populates="rfq", cascade="all, delete-orphan")
    items = relationship("ItemDetail", back_populates="rfq", cascade="all, delete-orphan")
    emails = relationship("Email", back_populates="rfq", cascade="all, delete-orphan")

class Location(db.Model):
    __tablename__ = 'locations'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    country = Column(String(100), nullable=False)
    city = Column(String(100), nullable=True)
    zip_code = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    vendor_id = Column(String(36), ForeignKey('vendors.id'), nullable=False)
    
    vendor = relationship("Vendor", back_populates="location")

class VendorPerformance(db.Model):
    __tablename__ = 'vendor_performances'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    response_time_avg = Column(Float, nullable=True)
    quality_rating = Column(Float, nullable=True)
    pricing_consistency = Column(Float, nullable=True)
    reliability_score = Column(Float, nullable=True)
    vendor_id = Column(String(36), ForeignKey('vendors.id'), nullable=False)
    
    vendor = relationship("Vendor", back_populates="performance")

class VendorSpecialization(db.Model):
    __tablename__ = 'vendor_specializations'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    specialization = Column(String(100), nullable=False)
    vendor_id = Column(String(36), ForeignKey('vendors.id'), nullable=False)

class VendorBrand(db.Model):
    __tablename__ = 'vendor_brands'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    brand = Column(String(100), nullable=False)
    vendor_id = Column(String(36), ForeignKey('vendors.id'), nullable=False)

class Vendor(db.Model):
    __tablename__ = 'vendors'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    vendor_type = Column(SQLEnum(VendorType), nullable=False)
    website = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    
    location = relationship("Location", uselist=False, back_populates="vendor", cascade="all, delete-orphan")
    performance = relationship("VendorPerformance", uselist=False, back_populates="vendor", cascade="all, delete-orphan")
    specializations = relationship("VendorSpecialization", cascade="all, delete-orphan")
    brands_carried = relationship("VendorBrand", cascade="all, delete-orphan")
    emails = relationship("Email", back_populates="vendor", cascade="all, delete-orphan")

class EmailTemplate(db.Model):
    __tablename__ = 'email_templates'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    country_code = Column(String(5), nullable=False)
    subject_template = Column(Text, nullable=False)
    body_template = Column(Text, nullable=False)
    signature = Column(Text, nullable=False)
    incoterms = Column(String(100), nullable=True)
    currency = Column(String(3), nullable=True)
    additional_notes = Column(Text, nullable=True)

class EmailAttachment(db.Model):
    __tablename__ = 'email_attachments'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    file_path = Column(String(255), nullable=False)
    email_id = Column(String(36), ForeignKey('emails.id'), nullable=False)

class Email(db.Model):
    __tablename__ = 'emails'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rfq_id = Column(String(36), ForeignKey('rfqs.id'), nullable=False)
    vendor_id = Column(String(36), ForeignKey('vendors.id'), nullable=False)
    subject = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    status = Column(SQLEnum(EmailStatus), default=EmailStatus.DRAFT)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    rfq = relationship("RFQ", back_populates="emails")
    vendor = relationship("Vendor", back_populates="emails")
    attachments = relationship("EmailAttachment", cascade="all, delete-orphan")