from typing import List, Dict, Any, Optional
import re
import math
from models import Vendor, VendorType, ItemDetail

def find_vendors_for_items(items: List[ItemDetail], vendors: List[Vendor]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Find suitable vendors for a list of items
    
    Args:
        items: List of items from an RFQ
        vendors: List of available vendors
        
    Returns:
        Dictionary mapping item IDs to lists of matching vendors with match scores
    """
    item_vendor_matches = {}
    
    for item in items:
        matching_vendors = []
        
        # Calculate matching score for each vendor
        for vendor in vendors:
            match_score = calculate_vendor_match_score(item, vendor)
            if match_score > 0:
                matching_vendors.append({
                    "vendor": vendor.dict(),
                    "match_score": match_score
                })
        
        # Sort vendors by match score (descending)
        matching_vendors.sort(key=lambda x: x["match_score"], reverse=True)
        
        # Store results
        item_vendor_matches[item.id] = matching_vendors
    
    return item_vendor_matches

def calculate_vendor_match_score(item: ItemDetail, vendor: Vendor) -> float:
    """
    Calculate a match score between an item and a vendor
    
    Args:
        item: An item from an RFQ
        vendor: A vendor to match against
        
    Returns:
        Match score (0-100)
    """
    score = 0
    
    # Check if the vendor carries the brand
    if item.brand and any(brand.lower() == item.brand.lower() for brand in vendor.brands_carried):
        score += 40
    
    # Check if the vendor specializes in the item's type or category
    if item.type:
        for specialization in vendor.specializations:
            if item.type.lower() in specialization.lower() or specialization.lower() in item.type.lower():
                score += 30
                break
    
    # Check if the item name matches vendor specializations
    if item.name:
        for specialization in vendor.specializations:
            if any(word.lower() in specialization.lower() for word in item.name.split()):
                score += 20
                break
    
    # Add points for vendor performance if available
    if vendor.performance:
        perf_score = (
            (vendor.performance.quality_rating or 0) +
            (vendor.performance.reliability_score or 0) +
            (vendor.performance.pricing_consistency or 0)
        ) / 15  # Max possible is 15 (3 * 5)
        
        score += perf_score * 10  # Add up to 10 points for performance
    
    return score

def search_vendors_by_criteria(
    vendors: List[Vendor],
    keywords: Optional[str] = None,
    country: Optional[str] = None,
    city: Optional[str] = None,
    zip_code: Optional[str] = None,
    vendor_type: Optional[VendorType] = None,
    radius_miles: Optional[int] = None
) -> List[Vendor]:
    """
    Search vendors based on various criteria
    
    Args:
        vendors: List of available vendors
        keywords: Search keywords
        country: Filter by country
        city: Filter by city
        zip_code: Filter by zip code
        vendor_type: Filter by vendor type
        radius_miles: If zip_code provided, find vendors within this radius
        
    Returns:
        List of matching vendors
    """
    matching_vendors = []
    
    for vendor in vendors:
        # Check if vendor matches all criteria
        if vendor_type and vendor.vendor_type != vendor_type:
            continue
        
        if country and vendor.location.country.lower() != country.lower():
            continue
        
        if city and (not vendor.location.city or vendor.location.city.lower() != city.lower()):
            continue
        
        if zip_code and radius_miles:
            # If zip code and radius provided, check if vendor is within radius
            if not vendor.location.zip_code or not is_within_zip_radius(zip_code, vendor.location.zip_code, radius_miles):
                continue
        elif zip_code:
            # If only zip code provided, exact match
            if not vendor.location.zip_code or vendor.location.zip_code != zip_code:
                continue
        
        # Check if vendor matches keywords
        if keywords:
            keyword_list = [k.strip().lower() for k in keywords.split(',')]
            keyword_match = False
            
            # Check against vendor name, specializations, and brands
            for keyword in keyword_list:
                if keyword in vendor.name.lower():
                    keyword_match = True
                    break
                
                for spec in vendor.specializations:
                    if keyword in spec.lower():
                        keyword_match = True
                        break
                
                for brand in vendor.brands_carried:
                    if keyword in brand.lower():
                        keyword_match = True
                        break
            
            if not keyword_match:
                continue
        
        # If we got here, vendor matches all criteria
        matching_vendors.append(vendor)
    
    return matching_vendors

def is_within_zip_radius(zip1: str, zip2: str, radius_miles: int) -> bool:
    """
    Check if two zip codes are within a given radius
    
    In a real implementation, this would use geolocation services.
    For this prototype, we'll use a simple check based on zip code patterns.
    
    Args:
        zip1: First zip code
        zip2: Second zip code
        radius_miles: Radius in miles
        
    Returns:
        True if within radius, False otherwise
    """
    # For US zip codes, we can estimate based on first 3 digits
    if re.match(r'^\d{5}$', zip1) and re.match(r'^\d{5}$', zip2):
        # Get first 3 digits
        z1 = int(zip1[:3])
        z2 = int(zip2[:3])
        
        # Very rough approximation - each zip3 is about 30 miles
        distance_estimate = abs(z1 - z2) * 30
        return distance_estimate <= radius_miles
    
    # For UK postcodes, check first two characters
    elif (re.match(r'^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$', zip1, re.IGNORECASE) and 
          re.match(r'^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$', zip2, re.IGNORECASE)):
        # Extract the outward code (first part)
        z1 = re.match(r'^([A-Z]{1,2}[0-9][A-Z0-9]?)', zip1, re.IGNORECASE).group(1)
        z2 = re.match(r'^([A-Z]{1,2}[0-9][A-Z0-9]?)', zip2, re.IGNORECASE).group(1)
        
        # Simple check if they're the same
        if z1 == z2:
            return True
        else:
            # Very rough approximation - if they share the first character, consider within 50 miles
            return z1[0] == z2[0] and radius_miles >= 50
    
    # For other cases, just check if they're identical
    return zip1 == zip2
