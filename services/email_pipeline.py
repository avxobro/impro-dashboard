from typing import List, Tuple, Dict, Optional
from services.content_verifier import ContentVerifier
from services.send_notification import WhatsAppSender
from services.document_processor import process_document
from services.email_modifier import EmailModifier
from db_utils import store_rfq_items_in_db

import os
from models import FileType 


class RFQPipeline:
    def __init__(self):
        print("🔄 Initializing ContentVerifier...")
        self.verifier = ContentVerifier()
        print("✅ ContentVerifier initialized")

        print("🔄 Initializing WhatsAppSender...")
        try:
            self.whatsapp_sender = WhatsAppSender(
                twilio_sid=os.getenv("TWILIO_SID"),
                twilio_token=os.getenv("TWILIO_AUTH_TOKEN"),
                whatsapp_number=os.getenv("WHATSAPP_NUMBER")
            )
            print("✅ WhatsAppSender initialized")
        except Exception as e:
            print(f"⚠️ WhatsApp initialization failed: {str(e)}")
            self.whatsapp_sender = None

    async def process(self, body: str, attachment_path: Optional[str] = None, email_metadata: Optional[Dict] = None):
        print("🔄 RFQPipeline processing started...")
        text_content = body
        print(f"📝 Email body length: {len(body)} characters")

        # Process attachment if present
        if attachment_path:
            print(f"🔄 Processing attachment: {attachment_path}")
            try:
                file_ext = os.path.splitext(attachment_path)[1].lower().replace('.', '')
                print(f"📄 File extension detected: {file_ext}")
                file_type = FileType(file_ext)
                extracted_items = await process_document(attachment_path, file_type)
                if extracted_items:
                    print(f"✅ Extracted {len(extracted_items)} items from attachment")
                    extracted_text = "\n\n".join(
                        [f"{item.name} (Qty: {item.quantity or 'N/A'})\n{item.description or 'No description'}"
                         for item in extracted_items]
                    )
                    text_content += "\n\n" + extracted_text
                    print(f"📝 Combined text content length: {len(text_content)} characters")
                else:
                    print("⚠️ No items extracted from attachment")
            except Exception as e:
                print(f"⚠️ Attachment processing failed: {str(e)}")
                import traceback
                print(traceback.format_exc())

        # Generate RFQ items using ContentVerifier
        print("🔄 Calling ContentVerifier to generate RFQ items...")
        items, is_rfq = self.verifier.generate_rfq(text_content)
        print(f"📊 RFQ verification result: {'✅ Valid RFQ' if is_rfq else '❌ Not an RFQ'}")
        print(f"📊 Items extracted: {len(items)}")

        if not is_rfq or not items:
            print("📭 Not an RFQ or no valid items found.")
            return []

        # Log extracted items
        print("📋 Items extracted from RFQ:")
        for i, item in enumerate(items):
            print(f"  {i+1}. {item.name} (Qty: {item.quantity or 'N/A'})")
            print(f"     Description: {item.description or 'No description'}")

        # Format and send WhatsApp message
        if self.whatsapp_sender:
            print("🔄 Preparing WhatsApp message...")
            message = "🧾 *RFQ Detected*\n" + "\n".join(
                [f"- {item.name} (Qty: {item.quantity or 'N/A'})\n  {item.description or 'No description'}"
                 for item in items]
            )
            print("📱 Sending WhatsApp notification...")
            success = self.whatsapp_sender.send_message(message)
            if success:
                print("✅ WhatsApp notification sent successfully")
            else:
                print("⚠️ Failed to send WhatsApp notification")
        else:
            print("⚠️ WhatsApp notification skipped: sender not initialized")

        # Store items in database if we have email metadata
        if email_metadata and is_rfq and items:
            try:
                print("💾 Storing RFQ items in database...")
                store_rfq_items_in_db(
                    items=items,
                    email_subject=email_metadata.get("subject", "No Subject"),
                    sender_name=email_metadata.get("sender_name", ""),
                    sender_email=email_metadata.get("sender_email", "Unknown Sender"),
                    body=email_metadata.get("body", "")
                )
                print("✅ RFQ items stored in database successfully")
            except Exception as e:
                print(f"❌ Error storing items in database: {str(e)}")
                import traceback
                print(traceback.format_exc())

        print("✅ RFQPipeline processing completed")
        return items