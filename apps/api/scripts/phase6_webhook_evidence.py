import asyncio
import hmac
import hashlib
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from uuid import uuid4

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

from app.services.webhook_delivery import deliver_webhook, verify_webhook_signature

SECRET = "phase6-local-webhook-secret"
captured = {}

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers["Content-Length"])
        body = self.rfile.read(length)
        captured["valid"] = verify_webhook_signature(
            secret=SECRET,
            timestamp=self.headers["X-LMS-Timestamp"],
            body=body,
            signature=self.headers["X-LMS-Signature"],
        )
        captured["event"] = self.headers["X-LMS-Event"]
        captured["event_id"] = self.headers["X-LMS-Event-Id"]
        captured["payload"] = json.loads(body)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")
    def log_message(self, format, *args):
        return

async def main():
    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}/webhook"
    event_id = uuid4()
    tenant_id = uuid4()
    await deliver_webhook(
        url=url,
        secret=SECRET,
        event_type="notification.created",
        event_id=event_id,
        tenant_id=tenant_id,
        payload={"id": "demo-1", "type": "course.completed"},
    )
    server.shutdown()
    print("LOCAL_WEBHOOK_HTTP_HANDSHAKE=PASS")
    print("SIGNATURE_VERIFIED=", captured["valid"])
    print("EVENT=", captured["event"])
    print("EVENT_ID_MATCH=", captured["event_id"] == str(event_id))
    print("PAYLOAD=", captured["payload"])

asyncio.run(main())
