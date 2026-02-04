# Webhook receiver + dashboard – plan

## Goal

- Use this Flask app on Render (free tier) as a **webhook receiver** for your monitoring system.
- Store every received alarm event in **persistent, free, queryable storage** (no local disk).
- Provide a **dashboard** to inspect timestamps, full JSON payloads, and link RAISED ↔ CLEARED by `alarmId`.

---

## 1. Storage choice (free, simple, thousands of records)

| Option | Pros | Cons |
|--------|------|------|
| **Supabase (PostgreSQL)** | Free tier (500MB), real DB, query by `alarmId`/time/state, JSONB for full payload, simple Python client | One-time signup at supabase.com |
| Google Sheets | Familiar, free | Rate limits, 10M cells limit, awkward for JSON and querying; more of a hack |
| MongoDB Atlas | Free 512MB, good for JSON | Slightly more setup than Supabase for this use case |

**Recommendation: Supabase.** Free, not convoluted, and built for exactly this: store many records, index by `alarmId` and timestamps, keep full JSON, and query “all events for this alarm” or “all RAISED in last 24h”.

---

## 2. Data model (Supabase)

Single table: **alarm_events**

| Column | Type | Purpose |
|--------|------|--------|
| `id` | uuid (default gen_random_uuid()) | Primary key |
| `received_at` | timestamptz | When our app received the webhook |
| `alarm_id` | text | Your `alarmId` – used to link RAISED ↔ CLEARED |
| `state` | text | `RAISED` or `CLEARED` |
| `payload` | jsonb | Full webhook JSON (for “walking through” in dashboard) |
| (optional) | | `raised_time`, `cleared_time` from payload for easier sorting/filtering |

Indexes: `alarm_id`, `received_at`, and optionally `state` so the dashboard and “link open/close” stay fast with thousands of rows.

---

## 3. App design

### 3.1 Webhook endpoint

- **POST /webhook/alarms** (or `/webhook` if you prefer a single endpoint)
  - Accept JSON body (your alarm payload).
  - Validate minimally (e.g. required fields: `alarmId`, `state`).
  - Insert one row into `alarm_events` (with `received_at = now()`, `alarm_id`, `state`, `payload` = full body).
  - Return 200 + minimal JSON so the monitoring system is happy (e.g. `{"ok": true, "id": "..."}`).

- Optional: **GET /webhook/alarms/health** returning 200 so Render/monitoring can ping “is the app up?”.

### 3.2 Dashboard (browser)

- **GET /** or **GET /dashboard**
  - List **alarm events** (newest first by default):
    - Table: received_at, alarm_id, state, rule, severity, raised/cleared times (from payload), link to “view JSON”.
  - Filters (query params or simple form):
    - By `alarm_id` (show all events for one alarm – RAISED + CLEARED).
    - By `state` (RAISED / CLEARED).
    - By time range (e.g. last 24h, last 7 days).
  - **Detail view** per event: full JSON payload (pretty-printed, collapsible if we add a bit of JS).
  - **“Open/close pairing”**: for a given `alarm_id`, show RAISED and CLEARED together (e.g. one row per alarm with “opened at … / cleared at …” or a timeline).

No auth in the first version to keep it simple; we can add a shared secret or basic auth later if you expose the dashboard.

---

## 4. Config and secrets (Render)

- **Supabase**
  - Create a free project at supabase.com.
  - Get **Project URL** and **anon (or service_role) key** from Project Settings → API.
  - In Render: Environment → add:
    - `SUPABASE_URL`
    - `SUPABASE_KEY`

- **Optional (later)**  
  - `WEBHOOK_SECRET` – if the monitoring system can send a header/token, we verify it before writing.

---

## 5. Implementation order

1. **Supabase**
   - Create project, create table `alarm_events` + indexes (we can provide SQL).
   - Add `SUPABASE_URL` and `SUPABASE_KEY` in Render.

2. **Flask**
   - Add `POST /webhook/alarms`: parse JSON, insert into Supabase, return 200.
   - Add dependency: `supabase` (or `httpx` + REST if you prefer minimal deps).

3. **Dashboard**
   - List page with filters (alarm_id, state, time).
   - Detail page: one event → full JSON.
   - “Alarm pair” view: for one `alarm_id`, show RAISED + CLEARED with timestamps.

4. **Polish**
   - Health endpoint, error handling, optional webhook secret.

---

## 6. What we’re not deciding yet (“and probably more”)

- Exact filters and columns you want in the table view.
- Whether you need export (CSV/JSON) or alerts (e.g. email when CLEARED).
- Auth for the dashboard (e.g. Render’s basic auth or a shared secret).

We can add these once the core webhook + storage + dashboard (timestamps, JSON view, open/close linking) are in place.

---

## 7. Payload note

Your examples use `state: "RAISED"` and `state: "CLEARED"` and the same `alarmId` for a pair. We’ll key linking on `alarm_id` and optionally use `raisedTime` / `clearedTime` from the payload for display and sorting. If you have more payload examples (e.g. other alarm types or fields you care about), we can align the table columns and dashboard with them in the next step.

If this plan works for you, next step is: create the Supabase table SQL and implement the webhook endpoint, then the dashboard. If you prefer Google Drive or another store, we can adjust the plan accordingly.
