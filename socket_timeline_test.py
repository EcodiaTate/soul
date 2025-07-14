# socket_timeline_test.py

import socketio

# Use your deployed server URL, port 80 or 443, no /api at the end
SOCKET_URL = "https://ecodia.au"

sio = socketio.Client()

@sio.on('timeline_update')
def on_timeline_update(data):
    print("🚀 Live timeline_update received:")
    print(data)

def main():
    print("Connecting to socket server...")
    sio.connect(SOCKET_URL)
    print("Connected! Waiting for timeline updates...")
    sio.wait()  # Keep the client running to listen

if __name__ == "__main__":
    main()
