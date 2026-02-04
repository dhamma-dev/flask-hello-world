# README

Flask app for [Render](https://render.com), used as a **webhook receiver** for alarm events (RAISED/CLEARED) with a simple dashboard.

## POC storage

Events are stored **in memory** (no persistence across restarts). See [PLAN.md](PLAN.md) for adding Supabase or other persistent storage.

## Run locally

```bash
pip install -r requirements.txt
python scripts/add_user.py admin yourpassword   # create users.txt (optional)
python app.py
```

- **Dashboard:** http://127.0.0.1:5000/ (login required)
- **Login:** flat file `users.txt` (one line per user: `username:werkzeug_hash`). Create users with `python scripts/add_user.py <username> <password>`. Override path with `USER_FILE`.
- **Health:** GET http://127.0.0.1:5000/webhook/alarms/health
- **Webhook:** POST http://127.0.0.1:5000/webhook/alarms (no auth) with JSON body (e.g. `alarmId`, `state`, `rule`, …)

Set `SECRET_KEY` in production for secure sessions. The dashboard auto-refreshes every 5s; check "Pause auto-refresh" to stop updates while you interact.

## Deployment

Follow the guide at https://render.com/docs/deploy-flask. Set the start command to `gunicorn app:app` (or as Render suggests). Set **SECRET_KEY** in the Render environment. For users: create `users.txt` in the repo (with hashed passwords from `add_user.py`) or use a build step that writes it; the app reads `USER_FILE` (default `users.txt`) from the project root.
