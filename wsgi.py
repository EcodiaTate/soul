# wsgi.py
from app import create_app, socketio

app = create_app()
application = app  # For Gunicorn

#if __name__ == "__main__":
 #   socketio.run(app, debug=True)
