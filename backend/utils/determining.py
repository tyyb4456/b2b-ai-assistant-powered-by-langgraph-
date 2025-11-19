def determine_cultural_region(location: str) -> str:
    """Determine cultural communication region based on supplier location"""
    location_lower = location.lower()
    
    if any(country in location_lower for country in ['china', 'japan', 'korea', 'taiwan', 'singapore', 'hong kong']):
        return 'east_asian'
    elif any(country in location_lower for country in ['india', 'pakistan', 'bangladesh', 'sri lanka']):
        return 'south_asian'  
    elif any(country in location_lower for country in ['germany', 'italy', 'france', 'uk', 'netherlands', 'spain']):
        return 'european'
    elif any(country in location_lower for country in ['uae', 'turkey', 'egypt', 'saudi']):
        return 'middle_eastern'
    elif any(country in location_lower for country in ['mexico', 'brazil', 'argentina', 'colombia']):
        return 'latin_american'
    elif any(country in location_lower for country in ['usa', 'canada']):
        return 'north_american'
    else:
        return 'international'