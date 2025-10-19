from flask import Flask
from threading import Thread

app = Flask(__name__)


@app.route("/")
def home() -> str:
    return "Bot is alive!"


def start_keepalive() -> None:
    Thread(target=app.run, kwargs={"host": "0.0.0.0", "port": 8080}, daemon=True).start()
