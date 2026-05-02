"""Simple in-memory broadcast hub for Server-Sent Events (SSE)."""
import json
import queue
import threading

clients_lock = threading.Lock()
clients = []


def broadcast_event(event_type, data):
    """Push a JSON event to all connected SSE clients."""
    payload = json.dumps({"type": event_type, "data": data})
    with clients_lock:
        dead = []
        for q in clients:
            try:
                q.put_nowait(payload)
            except queue.Full:
                dead.append(q)
        for q in dead:
            if q in clients:
                clients.remove(q)

