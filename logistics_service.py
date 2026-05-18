import random

def get_nearby_pharmacies(location):
    pharmacies = [
        {"name": "Apollo Pharmacy", "stock": random.choice(["In Stock", "Low Stock", "Out of Stock"]), "distance": "1.2 km", "location": location},
        {"name": "MedPlus", "stock": "In Stock", "distance": "0.8 km", "location": location},
        {"name": "Netmeds Store", "stock": random.choice(["In Stock", "Out of Stock"]), "distance": "2.5 km", "location": location},
        {"name": "Wellness Forever", "stock": "In Stock", "distance": "3.1 km", "location": location},
        {"name": "Local Chemist & Druggist", "stock": "In Stock", "distance": "0.5 km", "location": location}
    ]
    return [p for p in pharmacies if p['stock'] != "Out of Stock"]

def get_nearby_hospitals(location):
    hospitals = [
        {"name": "AIIMS", "specialty": "Multi-specialty", "distance": "3.4 km", "location": location},
        {"name": "Fortis Hospital", "specialty": "Emergency Care", "distance": "5.1 km", "location": location},
        {"name": "Apollo Hospitals", "specialty": "Critical Care", "distance": "4.0 km", "location": location},
        {"name": "Manipal Hospital", "specialty": "General Medicine", "distance": "6.2 km", "location": location},
        {"name": "Narayana Health", "specialty": "Cardiology", "distance": "7.0 km", "location": location}
    ]
    return hospitals


def get_nearest_medical_support(severity, location):
    if severity > 5:
        return {"type": "Hospital", "locations": get_nearby_hospitals(location)}
    return {"type": "Medical Shop", "locations": get_nearby_pharmacies(location)}

def get_specialist_slots(specialist_type):
    doctors = [
        {"name": "Dr. Sharma", "experience": "15 years", "slots": ["10:00 AM", "02:00 PM"]},
        {"name": "Dr. Iyer", "experience": "8 years", "slots": ["11:30 AM", "04:00 PM", "05:00 PM"]},
    ]
    return doctors