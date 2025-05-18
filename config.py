import os
from dotenv import load_dotenv

# Load environment variables if .env file exists
if os.path.exists(".env"):
    load_dotenv()

# Simple config settings to avoid validation errors
class Settings:
    # Application settings
    APP_NAME = "ProcureIQ™ AI Procurement Automation System"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # File Upload Settings
    UPLOAD_FOLDER = "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    ALLOWED_EXTENSIONS = ["pdf", "docx", "xlsx", "xls", "jpg", "jpeg", "png"]
    
    # RFQ Numbering
    RFQ_PREFIX = "INQ13QP"
    RFQ_YEAR = "2025"
    
    # Azure Document Intelligence (for PDF processing)
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", "")
    AZURE_DOCUMENT_INTELLIGENCE_KEY = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY", "")

settings = Settings()
