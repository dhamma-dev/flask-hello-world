import os

from flask import Flask, request, jsonify, render_template, redirect, url_for, session

from auth import verify_user, login_required
from storage import store

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")


# ---------- Webhook (no auth so monitoring can POST) ----------

@app.route("/webhook/alarms", methods=["POST"])
def webhook_alarms():
    """Receive alarm events (RAISED/CLEARED). Store and return 200."""
    if not request.is_json:
        return jsonify({"ok": False, "error": "Content-Type must be application/json"}), 400
    payload = request.get_json()
    if not payload:
        return jsonify({"ok": False, "error": "Empty body"}), 400
    alarm_id = payload.get("alarmId")
    state = payload.get("state")
    if not alarm_id or not state:
        return jsonify({"ok": False, "error": "Missing alarmId or state"}), 400
    record = store.add_event(payload)
    return jsonify({"ok": True, "id": record["id"]}), 200


@app.route("/webhook/alarms/health", methods=["GET"])
def webhook_health():
    """Liveness for Render/monitoring."""
    return jsonify({"ok": True}), 200


# ---------- Auth ----------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", next=request.args.get("next"))
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    next_url = request.form.get("next") or url_for("index")
    if not username or not verify_user(username, password):
        return render_template("login.html", error="Invalid username or password", next=next_url), 401
    session["user"] = username
    return redirect(next_url)


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


# ---------- Dashboard (login required) ----------

@app.route("/")
@login_required
def index():
    """Dashboard: list alarm events with optional filters."""
    alarm_id = request.args.get("alarm_id", "").strip() or None
    state = request.args.get("state", "").strip() or None
    try:
        limit = min(int(request.args.get("limit", 100)), 500)
    except ValueError:
        limit = 100
    try:
        offset = max(0, int(request.args.get("offset", 0)))
    except ValueError:
        offset = 0
    events = store.get_events(alarm_id=alarm_id, state=state, limit=limit, offset=offset)
    return render_template(
        "dashboard.html",
        events=events,
        alarm_id_filter=alarm_id or "",
        state_filter=state or "",
        limit=limit,
        offset=offset,
        total=store.count(),
    )


@app.route("/api/events")
@login_required
def api_events():
    """JSON list of events for dashboard live refresh. Same query params as index."""
    alarm_id = request.args.get("alarm_id", "").strip() or None
    state = request.args.get("state", "").strip() or None
    try:
        limit = min(int(request.args.get("limit", 100)), 500)
    except ValueError:
        limit = 100
    try:
        offset = max(0, int(request.args.get("offset", 0)))
    except ValueError:
        offset = 0
    events = store.get_events(alarm_id=alarm_id, state=state, limit=limit, offset=offset)
    return jsonify({
        "events": events,
        "total": store.count(),
        "limit": limit,
        "offset": offset,
    })


@app.route("/event/<event_id>")
@login_required
def event_detail(event_id):
    """Single event: full JSON payload."""
    event = store.get_event_by_id(event_id)
    if not event:
        return "Event not found", 404
    return render_template("event_detail.html", event=event)


@app.route("/alarm/<alarm_id>")
@login_required
def alarm_pair(alarm_id):
    """All events for one alarm_id (RAISED + CLEARED pairing)."""
    events = store.get_events_by_alarm_id(alarm_id)
    if not events:
        return "No events found for this alarm", 404
    return render_template("alarm_pair.html", alarm_id=alarm_id, events=events)


if __name__ == "__main__":
    app.run(debug=True)
