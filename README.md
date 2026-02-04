# README

Flask app for [Render](https://render.com), used as a **webhook receiver** for alarm events (RAISED/CLEARED) with a simple dashboard.

## POC storage

Events are stored **in memory** (no persistence across restarts). See [PLAN.md](PLAN.md) for adding Supabase or other persistent storage.

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

- **Dashboard:** http://127.0.0.1:5000/
- **Health:** GET http://127.0.0.1:5000/webhook/alarms/health
- **Webhook:** POST http://127.0.0.1:5000/webhook/alarms with JSON body (e.g. `alarmId`, `state`, `rule`, …)

## Deployment

Follow the guide at https://render.com/docs/deploy-flask. Set the start command to `gunicorn app:app` (or as Render suggests).
