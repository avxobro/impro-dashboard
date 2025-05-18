from fastapi import APIRouter, Request, Form, Query, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional
import uuid
import datetime

from models import Vendor, VendorType, Location, VendorPerformance
from config import settings
from services.vendor_matcher import find_vendors_for_items, search_vendors_by_criteria

router = APIRouter(prefix="/vendors", tags=["Vendor Management"])
templates = Jinja2Templates(directory="templates")

# In-memory vendor database for demo
vendor_database = {}

# Mock vendor data for demonstration purposes
def initialize_mock_vendors():
    # Only initialize if empty and not in production
    if not vendor_database:
        vendors = [
            Vendor(
                id=str(uuid.uuid4()),
                name="TechSupplies Inc.",
                vendor_type=VendorType.AUTHORIZED_DISTRIBUTOR,
                location=Location(country="USA", city="New York", zip_code="11040"),
                website="https://techsupplies.example.com",
                email="contact@techsupplies.example.com",
                specializations=["Electronics", "IT Equipment"],
                brands_carried=["Dell", "HP", "Cisco"], # not such  needed
                performance=VendorPerformance(
                    response_time_avg=24.5,
                    quality_rating=4.8,
                    pricing_consistency=4.6,
                    reliability_score=4.7
                )
            ),
            Vendor(
                id=str(uuid.uuid4()),
                name="GlobalParts Ltd.",
                vendor_type=VendorType.RESELLER,
                location=Location(country="UK", city="London", zip_code="EC1A 1BB"),
                website="https://globalparts.example.com",
                email="sales@globalparts.example.com",
                specializations=["Mechanical Components", "Industrial Supplies"],
                brands_carried=["Bosch", "Siemens", "ABB"],
                performance=VendorPerformance(
                    response_time_avg=36.2,
                    quality_rating=4.5,
                    pricing_consistency=4.2,
                    reliability_score=4.4
                )
            ),
            Vendor(
                id=str(uuid.uuid4()),
                name="Asian Electronics Co.",
                vendor_type=VendorType.MANUFACTURER,
                location=Location(country="China", city="Shenzhen", zip_code="518000"),
                website="https://asianelec.example.com",
                email="info@asianelec.example.com",
                specializations=["Electronic Components", "PCB Assembly"],
                brands_carried=["Own Brand", "OEM Services"],
                performance=VendorPerformance(
                    response_time_avg=18.7,
                    quality_rating=4.3,
                    pricing_consistency=4.8,
                    reliability_score=4.2
                )
            ),
            Vendor(
                id=str(uuid.uuid4()),
                name="Indian Industrial Supplies",
                vendor_type=VendorType.STOCKIST,
                location=Location(country="India", city="Mumbai", zip_code="400001"),
                website="https://indiansupplies.example.com",
                email="business@indiansupplies.example.com",
                specializations=["Industrial Equipment", "Machinery Parts"],
                brands_carried=["Larsen & Toubro", "Tata", "Kirloskar"],
                performance=VendorPerformance(
                    response_time_avg=29.5,
                    quality_rating=4.1,
                    pricing_consistency=4.4,
                    reliability_score=4.0
                )
            )
        ]
        
        for vendor in vendors:
            vendor_database[vendor.id] = vendor


@router.get("/", response_class=HTMLResponse)
async def get_vendors_dashboard(request: Request):
    """Main vendors dashboard view"""
    initialize_mock_vendors()
    return templates.TemplateResponse(
        "vendor_matching.html",
        {"request": request, "title": "Vendor Matching", "vendors": list(vendor_database.values())}
    )

@router.get("/search", response_class=JSONResponse)
async def search_vendors(
    request: Request,
    keywords: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    zip_code: Optional[str] = Query(None),
    vendor_type: Optional[VendorType] = Query(None),
    radius_miles: Optional[int] = Query(None)
):
    """Search vendors based on various criteria"""
    initialize_mock_vendors()
    
    # Use the vendor matcher service to find matching vendors
    matching_vendors = search_vendors_by_criteria(
        list(vendor_database.values()),
        keywords=keywords,
        country=country,
        city=city,
        zip_code=zip_code,
        vendor_type=vendor_type,
        radius_miles=radius_miles
    )
    
    return {"vendors": [vendor.dict() for vendor in matching_vendors]}

@router.post("/match/{rfq_id}", response_class=JSONResponse)
async def match_vendors_to_rfq(request: Request, rfq_id: str):
    """Find suitable vendors for items in an RFQ"""
    from routes.rfq import rfq_database
    initialize_mock_vendors()
    
    if rfq_id not in rfq_database:
        raise HTTPException(status_code=404, detail="RFQ not found")
    
    rfq = rfq_database[rfq_id]
    if not rfq.items:
        raise HTTPException(status_code=400, detail="No items in RFQ to match vendors")
    
    # Find vendors matching the items in the RFQ
    vendors_for_items = find_vendors_for_items(
        rfq.items,
        list(vendor_database.values())
    )
    
    return {
        "status": "success",
        "rfq_number": rfq.rfq_number,
        "item_vendor_matches": vendors_for_items
    }

@router.get("/{vendor_id}", response_class=JSONResponse)
async def get_vendor_details(request: Request, vendor_id: str):
    """Get details of a specific vendor"""
    initialize_mock_vendors()
    
    if vendor_id not in vendor_database:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    return vendor_database[vendor_id].dict()

@router.post("/", response_class=JSONResponse)
async def create_vendor(request: Request, vendor: Vendor):
    """Create a new vendor"""
    initialize_mock_vendors()
    
    vendor_id = str(uuid.uuid4())
    vendor.id = vendor_id
    vendor_database[vendor_id] = vendor
    
    return {"status": "success", "vendor_id": vendor_id, "message": "Vendor created successfully"}
