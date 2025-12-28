from datetime import datetime

from geoalchemy2 import Geography
from app.extensions import db


class Incident(db.Model):
    __tablename__ = "incidents"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=False
    )

 
    status = db.Column(
        db.String(20),
        default="unverified"   # unverified / verified / false / resolved
    )


    confirmations = db.Column(db.Integer, default=0)
    trust_score = db.Column(db.Integer, default=1)

 
    priority_score = db.Column(db.Float, default=0.0)

  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def to_dict(self):
        """Serialize for REST & Socket.IO"""
        return {
            "id": self.id,
            "type": self.type,
            "description": self.description,
            "status": self.status,
            "confirmations": self.confirmations,
            "trust_score": self.trust_score,
            "priority_score": self.priority_score,
            "created_at": self.created_at.isoformat()
        }
