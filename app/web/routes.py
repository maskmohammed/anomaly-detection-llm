from flask import Flask, render_template
from app.database.repository import SQLiteRepository

app = Flask(__name__)

@app.route("/")
def index():
    db = SQLiteRepository()
    logs = db.get_last_logs(limit=10)
    latest_log = logs[0] if logs else None

    scores = [log[5] for log in reversed(logs)]
    labels = [f"#{log[0]}" for log in reversed(logs)]

    return render_template(
        "index.html",
        logs=logs,
        latest_log=latest_log,
        scores=scores,
        labels=labels
    )