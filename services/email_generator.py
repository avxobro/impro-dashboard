import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import uuid
import datetime
from typing import List, Dict, Any

from models import RFQ, Vendor, EmailTemplate, Email, EmailStatus
from config import settings

def generate_email_for_vendor(rfq: RFQ, vendor: Vendor, template: EmailTemplate, serial: int = 1) -> Email:
    """
    Generate an email for a vendor based on an RFQ and template
    
    Args:
        rfq: The RFQ object
        vendor: The vendor to generate email for
        template: The email template to use
        serial: Serial number for the email
        
    Returns:
        Generated Email object
    """
    # Create item list text
    item_list = ""
    for i, item in enumerate(rfq.items, 1):
        item_text = f"{i}. {item.name}"
        if item.quantity:
            item_text += f", Qty: {item.quantity}"
        if item.brand:
            item_text += f", Brand: {item.brand}"
        if item.model:
            item_text += f", Model: {item.model}"
        if item.size:
            item_text += f", Size: {item.size}"
        if item.type:
            item_text += f", Type: {item.type}"
        
        item_list += item_text + "\n"
    
    # Format subject
    subject = template.subject_template.format(
        rfq_number=rfq.rfq_number,
        serial=f"{serial:02d}",
        vendor_name=vendor.name,
        country=vendor.location.country
    )
    
    # Format body
    body = template.body_template.format(
        vendor_name=vendor.name,
        item_list=item_list,
        rfq_number=rfq.rfq_number
    )
    
    # Add signature and additional notes based on country
    body += "\n\n" + template.signature
    
    if template.additional_notes:
        body += "\n\n" + template.additional_notes
    
    if template.incoterms:
        body += f"\n\nIncoterms: {template.incoterms}"
    
    if template.currency:
        body += f"\nCurrency: {template.currency}"
    
    # Create email object
    email = Email(
        id=str(uuid.uuid4()),
        rfq_id=rfq.id,
        vendor_id=vendor.id,
        subject=subject,
        body=body,
        attachments=[file.file_path for file in rfq.files],
        status=EmailStatus.READY,
        created_at=datetime.datetime.now()
    )
    
    return email

async def send_email(email: Email):
    """
    Send an email using SMTP
    
    Args:
        email: Email object to send
    """
    try:
        # Get vendor email
        from routes.vendor import vendor_database
        if email.vendor_id not in vendor_database:
            email.status = EmailStatus.FAILED
            email.error_message = "Vendor not found"
            return
        
        vendor = vendor_database[email.vendor_id]
        recipient_email = vendor.email
        
        if not recipient_email:
            email.status = EmailStatus.FAILED
            email.error_message = "Vendor email not available"
            return
        
        # Create MIME message
        msg = MIMEMultipart()
        msg['From'] = settings.EMAIL_FROM
        msg['To'] = recipient_email
        msg['Subject'] = email.subject
        
        # Attach body
        msg.attach(MIMEText(email.body, 'plain'))
        
        # Attach files
        for attachment_path in email.attachments:
            if os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as file:
                    part = MIMEApplication(file.read(), Name=os.path.basename(attachment_path))
                    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                    msg.attach(part)
        
        # Send email using SMTP
        try:
            print(f"📧 Attempting to send email to {recipient_email}")
            # Check if SMTP settings are configured
            if not hasattr(settings, 'SMTP_HOST') or not settings.SMTP_HOST:
                print("⚠️ SMTP settings not configured, simulating email send")
                # Simulate sending if SMTP settings are not available
                pass
            else:
                # Use actual SMTP to send email
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                    server.starttls()
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                    server.send_message(msg)
                    print(f"✅ Email sent successfully to {recipient_email}")
        except Exception as smtp_error:
            print(f"❌ SMTP error: {smtp_error}")
            email.status = EmailStatus.FAILED
            email.error_message = f"SMTP error: {smtp_error}"
            return
        
        # Update email status
        email.status = EmailStatus.SENT
        email.sent_at = datetime.datetime.now()
        
    except Exception as e:
        email.status = EmailStatus.FAILED
        email.error_message = str(e)
