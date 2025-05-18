import sys
import asyncio
from app import app
from complete_email_service import process_unread_emails

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "email-service":
            print("Starting Email Notification Service...")
            from dotenv import load_dotenv
            import os
            load_dotenv()
            
            EMAIL_USER = os.getenv("EMAIL_ADDRESS")
            EMAIL_PASS = os.getenv("APP_PASSWORD")
            
            if not EMAIL_USER or not EMAIL_PASS:
                print("❌ EMAIL_ADDRESS and APP_PASSWORD must be set in .env or environment.")
                sys.exit(1)
                
            try:
                asyncio.run(process_unread_emails(EMAIL_USER, EMAIL_PASS, max_emails=2000))
                print("✅ Finished processing emails.")
            except Exception as e:
                import traceback
                print("❌ Unexpected error:")
                print(traceback.format_exc())
                sys.exit(1)
        elif sys.argv[1] == "test-whatsapp":
            print("Testing WhatsApp Notification...")
            # test_whatsapp()
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Available commands: email-service, test-whatsapp")
    else:
        print("Starting Web Application...")
        app.run(host="0.0.0.0", port=5000, debug=True)
