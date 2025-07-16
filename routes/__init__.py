# routes/__init__.py
from .agents import agents_bp
from .auth import auth_bp
from .chat import chat_bp
from .dreams import dreams_bp
from .events import events_bp
from .timeline import timeline_bp

def register_blueprints(app):
    """
    Register all API blueprints to the Flask app.
    Extend this as you add more route modules!
    """
    app.register_blueprint(agents_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(chat_bp, url_prefix='/api')
    app.register_blueprint(dreams_bp, url_prefix='/api')
    app.register_blueprint(events_bp, url_prefix='/api')
    app.register_blueprint(timeline_bp, url_prefix='/api')
