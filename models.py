from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

# RFQ Models
class RFQStatus(str, Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    READY = "ready"
    SENT = "sent"
    COMPLETED = "completed"

class FileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    EXCEL = "excel"
    IMAGE = "image"

class UploadedFile(BaseModel):
    id: str
    filename: str
    file_type: FileType
    upload_date: datetime
    file_path: str

class ItemDetail(BaseModel):
    id: str
    name: str
    quantity: Optional[int] = None
    description: Optional[str] = None


class RFQ(BaseModel):
    id: str
    rfq_number: str
    client_name: str
    created_at: datetime
    updated_at: datetime
    status: RFQStatus
    files: List[UploadedFile] = []
    items: List[ItemDetail] = []
    notes: Optional[str] = None

# Vendor Models
class VendorType(str, Enum):
    AUTHORIZED_DISTRIBUTOR = "authorized_distributor"
    RESELLER = "reseller"
    STOCKIST = "stockist"
    MANUFACTURER = "manufacturer"

class Location(BaseModel):
    country: str
    city: Optional[str] = None
    zip_code: Optional[str] = None
    address: Optional[str] = None

class VendorPerformance(BaseModel):
    response_time_avg: Optional[float] = None
    quality_rating: Optional[float] = None
    pricing_consistency: Optional[float] = None
    reliability_score: Optional[float] = None

class Vendor(BaseModel):
    id: str
    name: str
    vendor_type: VendorType
    location: Location
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    specializations: List[str] = []
    brands_carried: List[str] = []
    performance: Optional[VendorPerformance] = None

# Email Models
class EmailTemplate(BaseModel):
    id: str
    country_code: str
    subject_template: str
    body_template: str
    signature: str
    incoterms: Optional[str] = None
    currency: Optional[str] = None
    additional_notes: Optional[str] = None

class EmailStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    SENT = "sent"
    FAILED = "failed"

class Email(BaseModel):
    id: str
    rfq_id: str
    vendor_id: str
    subject: str
    body: str
    attachments: List[str] = []
    status: EmailStatus
    created_at: datetime
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
