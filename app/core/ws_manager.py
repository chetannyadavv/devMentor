from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # NOTE: in-memory, per-process. Fine for a single api container;
        # would need a different design (e.g. per-connection Redis
        # channels) if this ever ran behind multiple api replicas.
        self.connections: dict[str, list[WebSocket]] = {}

    async def connect(self, submission_id: str, websocket: WebSocket):
        await websocket.accept()
        self.connections.setdefault(submission_id, []).append(websocket)

    def disconnect(self, submission_id: str, websocket: WebSocket):
        conns = self.connections.get(submission_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns and submission_id in self.connections:
            del self.connections[submission_id]

    async def broadcast(self, submission_id: str, message: dict):
        for ws in list(self.connections.get(submission_id, [])):
            try:
                await ws.send_json(message)
            except Exception:
                pass  # connection likely already gone; cleaned up on disconnect


manager = ConnectionManager()
