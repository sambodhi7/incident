from flask import Flask
from app.config import Config
from app.extensions import db, migrate, socketio


def create_app():
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)

    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    socketio.init_app(flask_app, cors_allowed_origins="*")

    import app.models
    import app.sockets

    from app.routes import api_bp
    flask_app.register_blueprint(api_bp, url_prefix="/api")

    return flask_app
