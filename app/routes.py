from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from geoalchemy2.functions import ST_MakePoint, ST_DWithin

from app.extensions import db, socketio
from app.models import Incident
from app.services import (
    find_possible_duplicate,
    calculate_priority,
    evaluate_false_report,
)
from app.sockets import geo_room

api_bp = Blueprint("api", __name__)

@api_bp.route("/incidents", methods=["POST"])
def create_incident():
    data = request.get_json()

    incident_type = data.get("type")
    description = data.get("description", "")
    lat = data.get("lat")
    lng = data.get("lng")

    if not all([incident_type, lat, lng]):
        return jsonify({"error": "type, lat, lng required"}), 400

   
    duplicate = find_possible_duplicate(
        lat=lat,
        lng=lng,
        incident_type=incident_type,
        created_at=datetime.utcnow(),
    )

    if duplicate:
        return jsonify({
            "message": "Possible duplicate incident already exists",
            "existing_incident": duplicate.to_dict()
        }), 409

   
    incident = Incident(
        type=incident_type,
        description=description,
        location=ST_MakePoint(lng, lat),
        status="unverified"
    )

    db.session.add(incident)
    db.session.commit()

    
    calculate_priority(incident)
    db.session.commit()

 
    room = geo_room(lat, lng)
    socketio.emit(
        "incident:new",
        incident.to_dict(),
        to=room
    )

    return jsonify(incident.to_dict()), 201
