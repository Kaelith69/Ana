from flask import Flask
from threading import Thread
import logging

app = Flask(__name__)

# Silence the Werkzeug development-server banner and request logs
logging.getLogger("werkzeug").setLevel(logging.ERROR)


@app.route("/")
def home() -> str:
    return "Bot is alive!"


def start_keepalive() -> None:
    Thread(
        target=app.run,
        kwargs={"host": "0.0.0.0", "port": 8080, "use_reloader": False, "use_debugger": False},
        daemon=True,
    ).start()
