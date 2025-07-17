# wsgi.py — Entry Point for Gunicorn + Gevent

from app import create_app, socketio

app = create_app()
application = app  # For Gunicorn

# Optional: run directly for local testing
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
