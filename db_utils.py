import uuid
import datetime
from flask import current_app
from db_models import db, RFQ, ItemDetail
from models import RFQStatus
from config import settings

def store_rfq_items_in_db(items, email_subject, sender_name, sender_email, body=""):
    """
    Store RFQ items in the database.
    Creates a new RFQ record and associated ItemDetail records.
    Returns the created RFQ.
    """
    # Generate RFQ number
    prefix = settings.RFQ_PREFIX
    year = settings.RFQ_YEAR
    
    # Get the latest RFQ number to increment
    with current_app.app_context():
        last_rfq = RFQ.query.order_by(RFQ.rfq_number.desc()).first()
        if last_rfq and last_rfq.rfq_number.startswith(f"{prefix}-{year}-"):
            try:
                seq_num = int(last_rfq.rfq_number.split('-')[-1]) + 1
            except:
                seq_num = 1
        else:
            seq_num = 1
        
        rfq_number = f"{prefix}-{year}-{seq_num:05d}"
        
        # Create new RFQ
        new_rfq = RFQ(
            id=str(uuid.uuid4()),
            rfq_number=rfq_number,
            client_name=sender_name if sender_name else sender_email,
            notes=f"Auto-created from email: {email_subject}\n\nSender: {sender_email}\n\n{body[:500]}...",
            status=RFQStatus.READY
        )
        
        # Add to database
        db.session.add(new_rfq)
        db.session.commit()
        
        # Add items to database
        for item in items:
            # Create an item record with a new UUID
            db_item = ItemDetail(
                id=str(uuid.uuid4()),
                name=item.name,
                quantity=item.quantity,
                description=item.description,
                rfq_id=new_rfq.id
            )
            db.session.add(db_item)
        
        # Commit all items
        db.session.commit()
        
        print(f"✅ Created RFQ {rfq_number} with {len(items)} items in database")
        return new_rfq 