from fastapi import APIRouter, Request, Form, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional
import uuid
import datetime

from models import Email, EmailStatus, EmailTemplate
from config import settings
from services.email_generator import generate_email_for_vendor, send_email

router = APIRouter(prefix="/emails", tags=["Email Services"])
templates = Jinja2Templates(directory="templates")

# In-memory email database for demo
email_database = {}
email_template_database = {}

# Initialize email templates
def initialize_email_templates():
    if not email_template_database:
        templates = [
            EmailTemplate(
                id=str(uuid.uuid4()),
                country_code="US",
                subject_template="{rfq_number} from SL #{serial} – RFQ to {vendor_name}, {country}",
                body_template="""
Dear {vendor_name},

We are looking for the following items:

{item_list}

Please provide your best quotation including pricing, delivery time, and payment terms.

Thank you,
ProcureIQ Team
                """,
                signature="ProcureIQ Inc.\nAddress: 123 Procurement St, New York, NY 10001\nPhone: +1-555-123-4567",
                incoterms="FOB",
                currency="USD"
            ),
            EmailTemplate(
                id=str(uuid.uuid4()),
                country_code="CN",
                subject_template="{rfq_number} from SL #{serial} – RFQ to {vendor_name}, {country}",
                body_template="""
Dear {vendor_name},

We are looking for the following items:

{item_list}

Please provide your best quotation including pricing, delivery time, and payment terms.

Thank you,
ProcureIQ Team
                """,
                signature="ProcureIQ Inc.\nChina Office\nPhone: +86-555-123-4567",
                incoterms="Ex-works",
                currency="RMB"
            ),
            EmailTemplate(
                id=str(uuid.uuid4()),
                country_code="IN",
                subject_template="{rfq_number} from SL #{serial} – RFQ to {vendor_name}, {country}",
                body_template="""
Dear {vendor_name},

We are looking for the following items:

{item_list}

Please provide your best quotation including pricing, delivery time, and payment terms.
Please ensure all items are genuine and include data sheets and weight information.

Thank you,
ProcureIQ Team
                """,
                signature="ProcureIQ Inc.\nIndia Office\nPhone: +91-555-123-4567",
                incoterms="Ex-works",
                currency="INR",
                additional_notes="All prices must be GST inclusive. Please provide certificate of authenticity."
            ),
            EmailTemplate(
                id=str(uuid.uuid4()),
                country_code="GB",
                subject_template="{rfq_number} from SL #{serial} – RFQ to {vendor_name}, {country}",
                body_template="""
Dear {vendor_name},

We are looking for the following items:

{item_list}

Please provide your best quotation including pricing, delivery time, and payment terms.

Thank you,
ProcureIQ Team
                """,
                signature="ProcureIQ Inc.\nUK Office\nAddress: 123 Procurement St, London\nPhone: +44-555-123-4567",
                incoterms="DDP",
                currency="GBP"
            )
        ]
        
        for template in templates:
            email_template_database[template.id] = template

@router.get("/", response_class=HTMLResponse)
async def get_emails_dashboard(request: Request):
    """Main emails dashboard view"""
    initialize_email_templates()
    return templates.TemplateResponse(
        "email_composer.html",
        {"request": request, "title": "Email Services", "emails": list(email_database.values())}
    )

@router.get("/templates", response_class=JSONResponse)
async def get_email_templates():
    """Get all email templates"""
    initialize_email_templates()
    return {"templates": [template.dict() for template in email_template_database.values()]}

@router.get("/templates/{country_code}", response_class=JSONResponse)
async def get_email_template_by_country(country_code: str):
    """Get email template for a specific country"""
    initialize_email_templates()
    
    for template in email_template_database.values():
        if template.country_code.lower() == country_code.lower():
            return template.dict()
    
    # If no specific template, return default (US)
    for template in email_template_database.values():
        if template.country_code == "US":
            return template.dict()
    
    raise HTTPException(status_code=404, detail="Email template not found")

@router.post("/generate/{rfq_id}/{vendor_id}", response_class=JSONResponse)
async def generate_vendor_email(request: Request, rfq_id: str, vendor_id: str, serial: int = 1):
    """Generate email for a vendor based on RFQ items"""
    from routes.rfq import rfq_database
    from routes.vendor import vendor_database, initialize_mock_vendors
    
    initialize_email_templates()
    initialize_mock_vendors()
    
    if rfq_id not in rfq_database:
        raise HTTPException(status_code=404, detail="RFQ not found")
    
    if vendor_id not in vendor_database:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    rfq = rfq_database[rfq_id]
    vendor = vendor_database[vendor_id]
    
    # Find appropriate template
    template = None
    for t in email_template_database.values():
        if t.country_code == vendor.location.country:
            template = t
            break
    
    # If no country-specific template, use default (US)
    if not template:
        for t in email_template_database.values():
            if t.country_code == "US":
                template = t
                break
    
    if not template:
        raise HTTPException(status_code=404, detail="Email template not found")
    
    # Generate email
    email = generate_email_for_vendor(rfq, vendor, template, serial)
    email_database[email.id] = email
    
    return {"status": "success", "email_id": email.id, "email": email.dict()}

@router.post("/send/{email_id}", response_class=JSONResponse)
async def send_email_to_vendor(request: Request, email_id: str, background_tasks: BackgroundTasks):
    """Send an email to a vendor"""
    if email_id not in email_database:
        raise HTTPException(status_code=404, detail="Email not found")
    
    email = email_database[email_id]
    
    # Schedule email sending as a background task
    background_tasks.add_task(send_email, email)
    
    # Update email status
    email.status = EmailStatus.SENT
    email.sent_at = datetime.datetime.now()
    email_database[email_id] = email
    
    return {"status": "success", "message": "Email scheduled for sending"}

@router.get("/{email_id}", response_class=JSONResponse)
async def get_email_details(request: Request, email_id: str):
    """Get details of a specific email"""
    if email_id not in email_database:
        raise HTTPException(status_code=404, detail="Email not found")
    
    return email_database[email_id].dict()
