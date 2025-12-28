from datetime import datetime, timedelta, timezone

from geoalchemy2.functions import ST_DWithin, ST_MakePoint
from sqlalchemy import and_

from app.extensions import db
from app.models import Incident
from app .config import Config

DUPLICATE_RADIUS_METERS = Config.DUPLICATE_RADIUS_METERS
DUPLICATE_TIME_WINDOW = Config.DUPLICATE_TIME_WINDOW
FALSE_REPORT_TIME_LIMIT = Config.FALSE_REPORT_TIME_LIMIT


def find_possible_duplicate(lat, lng, incident_type, created_at):
 

    time_threshold = created_at - timedelta(minutes=DUPLICATE_TIME_WINDOW)

    duplicate = Incident.query.filter(
        and_(
            Incident.type == incident_type,
            Incident.created_at >= time_threshold,
            Incident.status != "resolved",
            ST_DWithin(
                Incident.location,
                ST_MakePoint(lng, lat),
                DUPLICATE_RADIUS_METERS
            )
        )
    ).first()

    return duplicate


from datetime import datetime, timezone

def calculate_priority(incident):
    severity_map = {
          "fire": 9,
        "medical": 8,
        "accident": 7,
        "infrastructure": 6,
        "disturbance": 5,
    }

    severity = severity_map.get(incident.type, 4)
    confidence = min(10, incident.confirmations + incident.trust_score)

    created_at = incident.created_at

    
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    age_minutes = (datetime.now(timezone.utc) - created_at).total_seconds() / 60

    if age_minutes < 5:
        urgency = 10
    elif age_minutes < 15:
        urgency = 7
    else:
        urgency = 4

    incident.priority_score = int(
        severity * 0.4 +
        confidence * 0.3 +
        urgency * 0.3
    )



def evaluate_false_report(incident: Incident):


    age_minutes = (datetime.now(timezone.utc) - incident.created_at).total_seconds() / 60

    if incident.confirmations == 0 and age_minutes > FALSE_REPORT_TIME_LIMIT:
        incident.status = "false"

    return incident.status
