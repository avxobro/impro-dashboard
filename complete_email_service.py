import os
import imaplib
import email
from email.header import decode_header
import asyncio
from services.email_pipeline import RFQPipeline
from datetime import datetime
from app import app  # Import Flask app for app context

async def process_unread_emails(email_user, email_pass, max_emails=2000):
    print("🔄 Connecting to IMAP server...")
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(email_user, email_pass)
    mail.select("inbox")

    result, data = mail.search(None, 'UNSEEN')  # Only unseen/unread emails
    email_ids = data[0].split()
    print(f"🔍 Found {len(email_ids)} unread email(s)")

    # Limit to only the first few (e.g., 2)
    email_ids = email_ids[:max_emails]
    pipeline = RFQPipeline()

    for i, email_id in enumerate(email_ids):
        print(f"📨 Fetching email {i + 1}/{len(email_ids)} (ID: {email_id.decode()})...")
        result, message_data = mail.fetch(email_id, "(RFC822)")
        raw_email = message_data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Decode subject
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8", errors="ignore")
        # print(f"📋 Subject: {subject}")

        # Extract sender
        sender = msg.get("From")
        sender_email = email.utils.parseaddr(sender)[1]
        sender_name = email.utils.parseaddr(sender)[0]

        # ✅ Filter by allowed sender
        # if sender_email.lower() != "isolutionbd@gmail.com":
        #     print(f"⛔ Skipping email from {sender_email} (not allowed sender)")
        #     continue

        print(f"👤 From: {sender_name} <{sender_email}>")
        body = ""
        attachments = []

        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue

            content_disposition = str(part.get("Content-Disposition"))
            content_type = part.get_content_type()

            if content_type == "text/plain" and "attachment" not in content_disposition:
                charset = part.get_content_charset() or "utf-8"
                try:
                    body += part.get_payload(decode=True).decode(charset, errors="ignore")
                except Exception as e:
                    print(f"⚠️ Error decoding body: {e}")
                print(f"📝 Extracted body: {len(body)} characters")

            elif "attachment" in content_disposition:
                filename = part.get_filename()
                if filename:
                    os.makedirs("attachments", exist_ok=True)
                    filepath = os.path.join("attachments", filename)
                    with open(filepath, "wb") as f:
                        f.write(part.get_payload(decode=True))
                    attachments.append(filepath)
                    print(f"📎 Saved attachment: {filename}")

        # Mark email as read
        mail.store(email_id, '+FLAGS', '\\Seen')
        print("✅ Marked email as read")

        # Process the email via pipeline
        attachment_path = attachments[0] if attachments else None
        print(f"🚦 Processing email {i + 1}/{len(email_ids)}: {subject}")
        try:
            # Pass email metadata for database storage
            email_metadata = {
                "subject": subject,
                "sender_name": sender_name,
                "sender_email": sender_email,
                "body": body
            }
            await pipeline.process(body, attachment_path, email_metadata=email_metadata)
        except Exception as e:
            print(f"❌ Error during pipeline processing: {e}")

    mail.logout()
    print("📴 IMAP session closed.")


if __name__ == "__main__":
    print("🚀 Starting RFQ Email Processor...")
    from dotenv import load_dotenv
    load_dotenv()

    EMAIL_USER = os.getenv("EMAIL_ADDRESS")
    EMAIL_PASS = os.getenv("APP_PASSWORD")

    if not EMAIL_USER or not EMAIL_PASS:
        print("❌ EMAIL_ADDRESS and APP_PASSWORD must be set in .env or environment.")
        exit(1)

    try:
        # Run the email processor with Flask app context for database access
        with app.app_context():
            asyncio.run(process_unread_emails(EMAIL_USER, EMAIL_PASS, max_emails=2000))
        print("✅ Finished processing emails.")
    except Exception as e:
        import traceback
        print("❌ Unexpected error:")
        print(traceback.format_exc())
        exit(1)
