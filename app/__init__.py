from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.extensions import db, migrate, socketio


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)

    import app.models
    import app.sockets

    from app.routes import api_bp
    
    app.register_blueprint(api_bp, url_prefix="/api")
 
    @app.route("/health")
    def health():
        return {"status": "ok"}

    return app
