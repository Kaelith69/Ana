from flask import Flask, Response
from threading import Thread
import logging

app = Flask(__name__)

# Silence the Werkzeug development-server banner and request logs
logging.getLogger("werkzeug").setLevel(logging.ERROR)


@app.after_request
def _add_security_headers(response: Response) -> Response:
    """Add minimal security headers to every response (Fix S3)."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/")
def home() -> str:
    return "Bot is alive!"


def start_keepalive() -> None:
    Thread(
        target=app.run,
        kwargs={"host": "0.0.0.0", "port": 8080, "use_reloader": False, "use_debugger": False},
        daemon=True,
    ).start()
