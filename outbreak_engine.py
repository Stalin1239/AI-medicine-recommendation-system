from database import session, TriageHistory
from datetime import datetime, timedelta
from sqlalchemy import func

def check_for_outbreaks(location_query="Mangaluru"):
    # Define 'outbreak' as 5+ cases of the same disease in 48 hours in one location
    forty_eight_hours_ago = datetime.now() - timedelta(hours=48)
    
    outbreaks = session.query(
        TriageHistory.disease_name,
        func.count(TriageHistory.id).label('case_count')
    ).filter(
        TriageHistory.created_at >= forty_eight_hours_ago,
        TriageHistory.location == location_query
    ).group_by(TriageHistory.disease_name).having(func.count(TriageHistory.id) > 5).all()
    
    return outbreaks # Returns a list of diseases currently spiking