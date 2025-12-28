from flask import request
from flask_socketio import join_room, leave_room

from app.extensions import socketio

def geo_room(lat, lng, precision=2):
    return f"geo_{round(lat, precision)}_{round(lng, precision)}"



@socketio.on("join_area")
def handle_join_area(data):
    lat = data.get("lat")
    lng = data.get("lng")

    if lat is None or lng is None:
        return

    room = geo_room(lat, lng)
    join_room(room)

   
    socketio.emit(
        "area_joined",
        {"room": room},
        to=request.sid
    )


@socketio.on("leave_area")
def handle_leave_area(data):
    lat = data.get("lat")
    lng = data.get("lng")

    if lat is None or lng is None:
        return

    room = geo_room(lat, lng)
    leave_room(room)
