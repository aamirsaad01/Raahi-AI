# Raahi AI (FYP) — Travel Planning + Safety Companion

Raahi AI is a full-stack system that helps travelers in Pakistan plan trips end-to-end:

- **Itinerary & POIs**: recommend destinations, generate day-by-day plans, show POIs with metadata/photos, and provide cost breakdown.
- **Packing**: generate packing items and export lists.
- **Safety**: hazard reporting + NDMA alert ingestion pipeline (scrape → store → (optional) AI enrichment).
- **Collaboration**: group features in the mobile app (chat/polls/expenses/photos) scaffolded for trip coordination.

This README is written for new team members to quickly understand **what’s implemented so far**, **where it lives**, and **how to run/demo it**.

## What’s in this repo

```
Raahi-AI/
├── backend_scripts/                 # Python backend + collectors + utilities
│   ├── api/                         # Flask REST API (auth, itinerary, etc.)
│   ├── api_collectors/              # POI enrichment + data pipelines
│   ├── ndma_scraper.py              # NDMA scraping utilities
│   ├── ndma_poller.py               # Poller/service-style runner
│   └── *.md / *.py                  # Setup docs + maintenance scripts
├── database/
│   └── postgresql/                  # SQL schema + migrations
├── mobile_app/                      # Flutter app (UI + API clients)
└── FRONTEND_DEVELOPER_SETUP.md      # Most complete setup doc (recommended)
```

## System architecture (high level)

**Flutter app** ↔ **Flask REST API** ↔ **PostgreSQL**

Separately:

- **POI pipeline** fills `points_of_interest` (OpenStreetMap → optional LLM enrichment → optional photos)
- **NDMA pipeline** fills `ndma_alerts` (scrape NDMA advisories → store → optional enrichment)

## What has been implemented so far

### Backend (Python/Flask)
- **Auth APIs**: user registration + login.
- **Itinerary APIs**:
  - destination recommendations based on user inputs
  - itinerary generation (day-by-day plan, POIs, costs)
  - itinerary CRUD (create/read/update/delete) and “get user itineraries”
- **POI services**:
  - POI matching logic (mood/activities/season/etc.)
  - POI pipeline utilities for collecting/enriching data into Postgres
- **Hazard/NDMA utilities**:
  - NDMA scraper + poller scripts
  - database migrations for NDMA tables and hazard coordinate support

Key code locations:
- **API server entry**: `backend_scripts/api/app.py`
- **Itinerary routes**: `backend_scripts/api/routes/itinerary.py`
- **Itinerary logic**: `backend_scripts/api/services/itinerary_generator.py`, `itinerary_recommender.py`
- **POI matching**: `backend_scripts/api/services/poi_matcher.py`
- **POI pipeline**: `backend_scripts/api_collectors/poi_pipeline.py`, `llm_enricher.py`
- **NDMA**: `backend_scripts/ndma_scraper.py`, `backend_scripts/ndma_poller.py`

### Database (PostgreSQL)
- Core tables for **users**, **itineraries**, **location mapping**, **packing/checklist**, **hazard reports**.
- Additional schema/migrations for **NDMA alerts** and hazard coordinates.

Start here:
- `database/README.md`
- `database/postgresql/db_init.sql` (base schema)
- `database/postgresql/update_itinerary_schema.sql` (itinerary-related updates)
- `database/postgresql/add_ndma_alerts_table.sql` (NDMA alerts table)
- `database/postgresql/migrations/` (incremental migrations)

### Mobile app (Flutter)
The app contains implemented screens/features for:
- **AI chat** (UI screens)
- **Itinerary** (destination selection, results, POI details, day details, routes map, cost breakdown)
- **Packing** (planner + results + export)
- **Hazards** (map, reporting, detail sheets, filters, “my reports”)
- **Emergency** (SOS setup, safe points, downloads/outbox/settings)
- **Collaboration** (create/join group, chat rooms, polls, expenses, members, photos)

Key code locations:
- `mobile_app/lib/features/itinerary/`
- `mobile_app/lib/features/hazard/`
- `mobile_app/lib/features/packing/`
- `mobile_app/lib/features/collaboration/`
- `mobile_app/lib/features/emergency/`

## How to run (recommended path)

For the most complete step-by-step instructions, follow:
- **`FRONTEND_DEVELOPER_SETUP.md`**

Below is a quick “team-member” version.

### 1) Create `.env` locally (do not commit)
`.env` is intentionally **not tracked**. Copy the template:

```bash
copy .env.example .env
```

Fill values like:

```env
DB_NAME=raahi_ai
DB_USER=postgres
DB_PASSWORD=CHANGE_ME
DB_HOST=localhost
DB_PORT=5432
```

Optional (only needed for enrichment/photo fetching):

```env
GEMINI_API_KEY=...
UNSPLASH_ACCESS_KEY=...
```

### 2) Setup the database schema
- Create database: `raahi_ai`
- Run schema scripts from `database/postgresql/` (see `database/README.md`)

### 3) Install backend dependencies

```bash
cd backend_scripts
pip install -r requirements.txt
```

### 4) Start the backend API

```bash
cd backend_scripts/api
python app.py
```

Base URL: `http://localhost:5000`

### 5) Run the mobile app

```bash
cd mobile_app
flutter pub get
flutter run
```

For real device testing: point the app to `http://<YOUR_PC_IP>:5000` (not `localhost`).

## API overview (what the app calls)

Base URL: `http://localhost:5000`

- **Auth**
  - `POST /api/auth/register`
  - `POST /api/auth/login`
- **Itinerary**
  - `POST /api/itinerary/recommend`
  - `POST /api/itinerary/generate`
  - `GET /api/itinerary/{id}`
  - `GET /api/itinerary/user/{user_id}`
  - `PUT /api/itinerary/{id}`
  - `DELETE /api/itinerary/{id}`
- **Health**
  - `GET /api/health`

Full details + examples:
- `backend_scripts/api/API_DOCUMENTATION.md`

## Data pipelines (POIs + NDMA)

### POI collection/enrichment
This fills `points_of_interest` in Postgres so itinerary generation can select real attractions.

```bash
cd backend_scripts/api_collectors
python poi_pipeline.py --limit 3
```

### NDMA alerts
The NDMA scripts scrape advisories and store them in Postgres (requires the NDMA table migration).

Start reading here:
- `backend_scripts/NDMA_POLLER_README.md`

## Demo flow for your FYP presentation

1. **Backend health**: open `http://localhost:5000/api/health`
2. **Register + login**: use app UI or call the auth endpoints
3. **Generate itinerary**: choose destination + constraints → show results screen + cost breakdown
4. **Hazard map/reporting**: show hazard map, filters, create a report, view “my reports”
5. **Packing**: generate packing list for trip parameters + export
6. (Optional) **Pipelines**:
   - run POI pipeline for a few locations
   - run NDMA poller/scraper and show DB table populated

## Important repo notes

- **Secrets**: never commit `.env`. Use `.env.example` as the template.
- **Line endings**: on Windows you may see CRLF/LF warnings; it’s normal as long as code runs.

## Pointers for new team members

- If you’re working on **backend**: start at `backend_scripts/api/app.py` and `backend_scripts/api/routes/`.
- If you’re working on **mobile**: start at `mobile_app/lib/routes/app_routes.dart` and the feature folders.
- If you’re working on **data pipelines**: start at `backend_scripts/api_collectors/poi_pipeline.py`.
- If you’re working on **NDMA/safety**: start at `backend_scripts/ndma_scraper.py` and `backend_scripts/ndma_poller.py`.

## Documentation index

- **Setup (recommended)**: `FRONTEND_DEVELOPER_SETUP.md`
- **Backend docs**: `backend_scripts/README.md`, `backend_scripts/api/API_DOCUMENTATION.md`
- **Database**: `database/README.md`
- **NDMA**: `backend_scripts/NDMA_POLLER_README.md`
