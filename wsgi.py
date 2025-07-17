import eventlet
eventlet.monkey_patch()
# wsgi.py
from app import create_app, socketio

app = create_app()
application = app  # For Gunicorn
