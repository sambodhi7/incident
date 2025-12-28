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
        created_at=datetime.now(timezone.utc),
    )

    
    if duplicate:
        duplicate.confirmations += 1
        duplicate.trust_score += 1
        calculate_priority(duplicate)
        db.session.commit()

        room = geo_room(lat, lng)
        socketio.emit(
            "incident:update",
            duplicate.to_dict(),
            to=room
        )

        return jsonify({
            "message": "Incident already exists. Report counted.",
            "incident": duplicate.to_dict()
        }), 200

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


@api_bp.route("/incidents/nearby", methods=["GET"])
def get_nearby_incidents():
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    radius = request.args.get("radius", 500, type=int)  # meters

    if lat is None or lng is None:
        return jsonify({"error": "lat and lng required"}), 400

    incidents = Incident.query.filter(
        Incident.status != "resolved",
        ST_DWithin(
            Incident.location,
            ST_MakePoint(lng, lat),
            radius
        )
    ).all()

    return jsonify([i.to_dict() for i in incidents])


@api_bp.route("/incidents/<int:incident_id>/confirm", methods=["POST"])
def confirm_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)

    incident.confirmations += 1
    incident.status = "verified"

    calculate_priority(incident)
    db.session.commit()

    lat = incident.location.y
    lng = incident.location.x
    room = geo_room(lat, lng)

    socketio.emit(
        "incident:update",
        incident.to_dict(),
        to=room
    )

    return jsonify(incident.to_dict())


@api_bp.route("/incidents/<int:incident_id>/false", methods=["POST"])
def mark_false_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)

    incident.status = "false"
    db.session.commit()

    lat = incident.location.y
    lng = incident.location.x
    room = geo_room(lat, lng)

    socketio.emit(
        "incident:update",
        incident.to_dict(),
        to=room
    )

    return jsonify({"status": "marked false"})


@api_bp.route("/incidents/evaluate-false", methods=["POST"])
def auto_evaluate_false():
    incidents = Incident.query.filter(
        Incident.status == "unverified"
    ).all()

    updated = []

    for incident in incidents:
        old_status = incident.status
        evaluate_false_report(incident)
        if incident.status != old_status:
            updated.append(incident)

    db.session.commit()

    for incident in updated:
        lat = incident.location.y
        lng = incident.location.x
        room = geo_room(lat, lng)

        socketio.emit(
            "incident:update",
            incident.to_dict(),
            to=room
        )

    return jsonify({
        "checked": len(incidents),
        "updated": len(updated)
    })


@api_bp.route("/admin/incidents", methods=["GET"])
def admin_get_all_incidents():
    incidents = Incident.query.filter(
        Incident.status != "resolved"
    ).order_by(Incident.priority_score.desc()).all()

    return jsonify([i.to_dict() for i in incidents])

@api_bp.route("/ping"):
def ping():
    return "1";