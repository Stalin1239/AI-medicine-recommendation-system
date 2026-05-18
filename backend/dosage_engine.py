def calculate_dosage(base_mg, weight_kg, age):
    """
    Implements Clark's Rule for children and weight-proportional scaling for adults.
    """
    if base_mg == 0: return "Consult Doctor"
    
    # Clark's Rule for children (approx under 12 or low weight)
    if age < 12 or weight_kg < 35:
        final_dose = (weight_kg / 70) * base_mg
        return f"{round(final_dose, 2)} mg (Pediatric Adjusted)"
    
    # Adult Scaling
    elif weight_kg > 90:
        return f"{base_mg} mg (Standard Adult Max - Monitor closely)"
    
    return f"{base_mg} mg (Standard Adult Dose)"