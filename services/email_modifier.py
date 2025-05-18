from typing import List, Optional
import os
import uuid
import PyPDF2
import docx
import pandas as pd
from config import settings
from models import ItemDetail, FileType
from services.content_verifier import ContentVerifier
from services.document_processor import process_document
from typing import List, Optional
import os
import uuid
import PyPDF2
import docx
import pandas as pd
from google.cloud import vision
from services.read_pdf import AzureAIPDFReader
from config import settings
from models import ItemDetail, FileType
from services.content_verifier import ContentVerifier
from typing import List, Optional
import os
import uuid
import PyPDF2
import docx
import pandas as pd
from google.cloud import vision
from services.read_pdf import AzureAIPDFReader
from config import settings
from models import ItemDetail, FileType
from services.content_verifier import ContentVerifier
import threading, time
import asyncio

class EmailModifier:
    def __init__(self):
        self.verifier = ContentVerifier()

    async def process_email(self, body: str, attachment_path: Optional[str] = None) -> str:
        text_content = body

        # Process the attachment if provided
        if attachment_path:
            try:
                file_type = FileType(os.path.splitext(attachment_path)[1].lower().replace('.', ''))
                extracted_items = await process_document(attachment_path, file_type)
                
                if extracted_items:
                    print("Extracted items Successfully")
                    extracted_text = "\n\n".join([f"{item.name} (Qty: {item.quantity or 'N/A'})\n{item.description or 'No description'}" for item in extracted_items])
                    text_content += "\n\n" + extracted_text
            except Exception as e:
                print(f"Attachment processing failed for {attachment_path}: {e}")

        # Extract items from the full text content
        items = self.verifier.generate_rfq(text_content)

        # Filter out invalid items
        valid_items = [item for item in items if item.name != "Unknown Item" and not item.name.startswith("Wrong Request")]

        if not valid_items:
            return "Not an RFQ"

        # Format the RFQ message
        message_lines = ["🧾 *RFQ Detected*"]
        for item in valid_items:
            message_lines.append(f"- {item.name} (Qty: {item.quantity or 'N/A'})\n  {item.description or 'No description'}")

        return "\n".join(message_lines)


def init_email_processor(app):
    """
    Initialize the email processor to run in the background.
    This function is imported by app.py to start the email monitoring service.
    
    Args:
        app: The Flask application instance
        
    Returns:
        threading.Thread: The background thread that's monitoring emails
    """
    def monitor_email():
        # Email credentials should be loaded from config or environment
        # For now using placeholder values
        email_user = os.environ.get("EMAIL_ADDRESS", "")
        email_pass = os.environ.get("APP_PASSWORD", "")
        
        if not email_user or not email_pass:
            print("⚠️ Email monitoring disabled: Missing credentials")
            return
            
        from complete_email_service import process_unread_emails
        
        with app.app_context():
            print("📧 Starting email monitoring service...")
            
            while True:
                try:
                    # Check for new emails
                    asyncio.run(process_unread_emails(email_user, email_pass, max_emails=5))
                    print("✅ Email check completed")
                except Exception as e:
                    print(f"❌ Error in email monitoring: {e}")
                    
                # Wait before checking again
                time.sleep(300)  # Check every 5 minutes
    
    # Start in a background thread
    email_thread = threading.Thread(target=monitor_email, daemon=True)
    email_thread.start()
    return email_thread