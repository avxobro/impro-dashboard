from fastapi import APIRouter, Request, Form, UploadFile, File, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional
import uuid
import os
import datetime
from pathlib import Path

from models import RFQ, RFQStatus, UploadedFile, FileType, ItemDetail
from config import settings
from services.document_processor import process_document

router = APIRouter(prefix="/rfq", tags=["RFQ Management"])
templates = Jinja2Templates(directory="templates")

# In-memory storage for demo purposes
rfq_database = {}
current_rfq_number = 1

def generate_rfq_number():
    """Generate a unique RFQ number"""
    now = datetime.datetime.now()
    return f"RFQ-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

def ensure_upload_dir_exists():
    """Ensure the upload directory exists"""
    os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)

@router.get("/", response_class=HTMLResponse)
async def get_rfq_dashboard(request: Request):
    """Main RFQ dashboard view"""
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "title": "RFQ Dashboard", "rfqs": list(rfq_database.values())}
    )

@router.get("/new", response_class=HTMLResponse)
async def new_rfq_form(request: Request):
    """Form to create a new RFQ"""
    return templates.TemplateResponse(
        "rfq_entry.html",
        {"request": request, "title": "New RFQ Entry"}
    )

@router.post("/new", response_class=HTMLResponse)
async def create_rfq(
    request: Request,
    client_name: str = Form(...),
    notes: Optional[str] = Form(None),
    files: List[UploadFile] = File(None)
):
    """Create a new RFQ with uploaded files"""
    ensure_upload_dir_exists()
    
    # Generate a unique RFQ ID and number
    rfq_id = str(uuid.uuid4())
    rfq_number = generate_rfq_number()
    now = datetime.datetime.now()
    
    # Process uploaded files
    uploaded_files = []
    if files:
        for file in files:
            if file.filename:
                # Determine file type
                file_extension = file.filename.split('.')[-1].lower()
                if file_extension in ['pdf']:
                    file_type = FileType.PDF
                elif file_extension in ['docx', 'doc']:
                    file_type = FileType.DOCX
                elif file_extension in ['xlsx', 'xls']:
                    file_type = FileType.EXCEL
                elif file_extension in ['jpg', 'jpeg', 'png', 'gif']:
                    file_type = FileType.IMAGE
                else:
                    continue  # Skip unsupported file types
                
                # Save file
                file_id = str(uuid.uuid4())
                file_path = f"{settings.UPLOAD_FOLDER}/{file_id}_{file.filename}"
                
                with open(file_path, "wb") as f:
                    f.write(await file.read())
                
                uploaded_file = UploadedFile(
                    id=file_id,
                    filename=file.filename,
                    file_type=file_type,
                    upload_date=now,
                    file_path=file_path
                )
                uploaded_files.append(uploaded_file)
    
    # Create the RFQ object
    new_rfq = RFQ(
        id=rfq_id,
        rfq_number=rfq_number,
        client_name=client_name,
        created_at=now,
        updated_at=now,
        status=RFQStatus.DRAFT,
        files=uploaded_files,
        notes=notes
    )
    
    # Store in our in-memory database
    rfq_database[rfq_id] = new_rfq
    
    return templates.TemplateResponse(
        "data_extraction.html",
        {
            "request": request,
            "title": "Data Extraction",
            "rfq": new_rfq,
            "message": f"RFQ {rfq_number} created successfully"
        }
    )

@router.get("/{rfq_id}", response_class=HTMLResponse)
async def get_rfq_details(request: Request, rfq_id: str):
    """Get details of a specific RFQ"""
    if rfq_id not in rfq_database:
        raise HTTPException(status_code=404, detail="RFQ not found")
    
    rfq = rfq_database[rfq_id]
    return templates.TemplateResponse(
        "data_extraction.html",
        {"request": request, "title": f"RFQ {rfq.rfq_number}", "rfq": rfq}
    )

@router.post("/{rfq_id}/process", response_class=JSONResponse)
async def process_rfq_documents(request: Request, rfq_id: str):
    """Process RFQ documents to extract text and generate RFQ items using AI"""
    if rfq_id not in rfq_database:
        raise HTTPException(status_code=404, detail="RFQ not found")
    
    rfq = rfq_database[rfq_id]
    print(f"\n=== PROCESSING RFQ: {rfq.rfq_number} ===")
    print(f"Client: {rfq.client_name}")
    print(f"Number of files: {len(rfq.files)}")
    
    # Update status
    rfq.status = RFQStatus.PROCESSING
    rfq_database[rfq_id] = rfq
    
    # Process each document to extract text and generate RFQ items
    extracted_items = []
    for idx, file in enumerate(rfq.files, 1):
        print(f"\nProcessing file {idx}/{len(rfq.files)}: {file.filename} (Type: {file.file_type})")
        try:
            # This now extracts content and uses AI to generate RFQ items
            items = await process_document(file.file_path, file.file_type)
            
            # Generate new UUIDs for the items before adding them to the RFQ
            for item in items:
                item.id = str(uuid.uuid4())  # Replace with a new UUID
                
            print(f"Extraction complete. Items created: {len(items)}")
            extracted_items.extend(items)
        except Exception as e:
            print(f"ERROR processing document: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")
    
    # Update RFQ with extracted content
    rfq.items = extracted_items
    rfq.status = RFQStatus.READY
    rfq.updated_at = datetime.datetime.now()
    rfq_database[rfq_id] = rfq
    
    print(f"\n=== PROCESSING COMPLETE ===")
    print(f"Total items extracted: {len(extracted_items)}")
    print(f"RFQ status updated to: {rfq.status}")
    
    # Convert items to dictionaries for the response
    items_data = []
    for item in extracted_items:
        items_data.append({
            "id": item.id,
            "name": item.name,
            "quantity": item.quantity,
            "description": item.description
        })
    
    return {
        "status": "success", 
        "message": "Documents processed successfully. AI has identified items from the documents.",
        "item_count": len(extracted_items),
        "items": items_data
    }

@router.put("/{rfq_id}/items", response_class=JSONResponse)
async def update_rfq_items(request: Request, rfq_id: str):
    """Update RFQ items after manual correction"""
    print(f"\n=== UPDATING RFQ ITEMS for {rfq_id} ===")
    
    # Check if RFQ exists
    if rfq_id not in rfq_database:
        print(f"RFQ {rfq_id} not found")
        raise HTTPException(status_code=404, detail="RFQ not found")
    
    rfq = rfq_database[rfq_id]
    print(f"Found RFQ: {rfq.rfq_number}")
    
    try:
        # Get the data from the request
        request_body = await request.body()
        print(f"Request body size: {len(request_body)} bytes")
        
        # Try to parse JSON
        try:
            items_data = await request.json()
            print(f"Successfully parsed JSON, received {len(items_data)} items")
        except Exception as e:
            print(f"Error parsing JSON: {str(e)}")
            print(f"Raw request body: {request_body.decode('utf-8', errors='replace')}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
        
        items = []
        
        # Process each item
        for idx, item_data in enumerate(items_data):
            print(f"Processing item {idx}: {item_data.get('name', 'No name')}")
            try:
                item = ItemDetail(
                    id=item_data.get('id', str(uuid.uuid4())),
                    name=item_data.get('name', 'Unnamed Item'),
                    quantity=item_data.get('quantity'),
                    description=item_data.get('description')
                )
                items.append(item)
            except Exception as e:
                print(f"Error creating item {idx}: {str(e)}")
                print(f"Item data: {item_data}")
                # Continue with other items instead of failing completely
        
        if not items:
            print("No valid items found in request")
            raise HTTPException(status_code=400, detail="No valid items provided")
        
        # Update RFQ with corrected items
        rfq.items = items
        rfq.updated_at = datetime.datetime.now()
        rfq_database[rfq_id] = rfq
        
        print(f"Successfully updated RFQ with {len(items)} items")
        return {"status": "success", "message": f"RFQ items updated successfully. Saved {len(items)} items."}
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
