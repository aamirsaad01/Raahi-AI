# Raahi AI FYP - Complete Project and Agentic AI Explanation

## 1) Project Overview

Raahi AI is a full-stack travel and safety platform focused on Pakistan tourism.  
It combines itinerary planning, hazard intelligence, emergency support, and an AI chat assistant in one system.

At a high level:
- **Mobile app (Flutter)** is the user-facing product.
- **Backend API (Flask/Python)** handles business logic and AI orchestration.
- **PostgreSQL** stores users, itineraries, chat history, hazard data, and safety resources.
- **External APIs and AI providers** (OpenAI, Geoapify, NDMA source site, geocoding) provide intelligence and live context.

Core user goals:
- Plan multi-day trips with realistic routes and costs.
- Chat with an assistant that understands profile + itinerary + hazards.
- Monitor and report hazards.
- Access emergency contacts and safe points.

---

## 2) High-Level Architecture

### Frontend (Mobile)
- Located under `mobile_app/lib/features/`.
- Feature-based modules: itinerary, ai_chat, hazard, emergency, risk_around, home/auth/navigation.
- API clients call backend endpoints such as:
  - `/api/itinerary/*`
  - `/api/chat/*`
  - `/api/hazards/*`
  - `/api/safe-points/*`

### Backend (Flask)
- Main entry: `backend_scripts/api/app.py`.
- Blueprints/routes:
  - `backend_scripts/api/routes/itinerary.py`
  - `backend_scripts/api/routes/chat.py`
  - `backend_scripts/api/routes/auth.py`
  - `backend_scripts/api/routes/emergency.py`
- Shared DB layer: `backend_scripts/api/utils/db_helper.py`.

### Database
- Base schema: `database/postgresql/db_init.sql`.
- Incremental migrations: `database/postgresql/migrations/`.
- AI-relevant tables include:
  - `itineraries`
  - `chat_sessions`, `chat_messages`
  - `hazard_reports`
  - `ndma_alerts_ai`
  - `itinerary_emergency_contacts`
  - `safe_points`

### Data Pipelines / Background Intelligence
- NDMA advisory ingestion:
  - `backend_scripts/ndma_scraper.py`
  - `backend_scripts/ai_alert_extractor.py`
  - `backend_scripts/ndma_poller.py`
- POI enrichment pipeline:
  - `backend_scripts/api_collectors/poi_pipeline.py`
  - `backend_scripts/api_collectors/openai_enricher.py`
  - `backend_scripts/api_collectors/llm_enricher.py`

---

## 3) What "Agentic AI" Means in This Project

In Raahi AI, "agentic AI" is not a single LLM call. It is an **orchestrated workflow** where the system:
1. Retrieves structured context from database.
2. Applies deterministic ranking/heuristics.
3. Uses external tools (for routing/travel times).
4. Calls the LLM with strict instructions and schema constraints.
5. Validates, repairs, and post-processes model output.
6. Persists and serves final results.

So the agent is a **Python orchestrator + LLM + tools + guardrails**, rather than a raw chatbot.

The strongest agentic implementation is:
- `backend_scripts/api/services/itinerary_agent.py`

Secondary agentic systems:
- `backend_scripts/api/chat/service.py` (context-aware conversational assistant)
- `backend_scripts/ai_alert_extractor.py` + `ndma_scraper.py` (AI extraction pipeline from NDMA PDFs)

---

## 4) Main Agentic Workflows

## 4.1 Itinerary Agent Workflow (Primary Agent)

Primary files:
- Route layer: `backend_scripts/api/routes/itinerary.py`
- Agent core: `backend_scripts/api/services/itinerary_agent.py`
- Tool adapter: `backend_scripts/api/services/routing_service.py`
- Retrieval/ranking: `backend_scripts/api/services/poi_matcher.py`
- DB access: `backend_scripts/api/utils/db_helper.py`

### Step-by-step flow

1. **User request enters API**
   - Mobile posts to `/api/itinerary/generate`.
   - Request contains destination/corridor, days, budget, mood, activities, month, people.

2. **Agent selection**
   - Route attempts `ItineraryAgent`.
   - If agent fails non-terminally, route can fall back to legacy `ItineraryGenerator`.
   - If terminal data issue occurs (unknown city/no POIs), returns explicit error (no fallback).

3. **Context retrieval**
   - For single-city: resolve destination in `location_mapping`.
   - Fetch POIs from `points_of_interest`.
   - For corridor mode: gather POIs across ordered corridor stops.

4. **Deterministic relevance filtering**
   - `POIMatcher.filter_and_rank_pois(...)` ranks POIs with non-LLM logic.
   - If too sparse, relaxed threshold logic adds additional POIs.

5. **Geographic planning heuristic**
   - Agent computes `suggested_visit_order` with nearest-neighbor style logic.
   - Uses haversine and route-cost selection to reduce backtracking.

6. **Hazard retrieval**
   - Pulls active/recent NDMA alerts from `ndma_alerts_ai`.
   - Injects hazard information into prompt context.

7. **Tool call for routing matrix**
   - Calls Geoapify route matrix through `RoutingService`.
   - Produces drive-time/distance matrix for POI pairs.
   - Adds this as explicit prompt input so LLM schedules realistic transit.

8. **LLM generation**
   - OpenAI chat completion (`OPENAI_MODEL`, default `gpt-4o-mini`).
   - Strict system prompt and JSON-only response format.
   - Prompt includes user profile, retrieved POIs, hazards, transit matrix.

9. **Validation and normalization**
   - Parse JSON output.
   - Enforce required schema keys.
   - Remove unknown `poi_id`s.
   - Normalize numbers, nulls, and expected field shapes.

10. **Post-LLM correction**
   - Enrich time slots with POI coordinates.
   - Recompute transit per consecutive slot using Geoapify leg calls.
   - If external route call fails, fallback to haversine + heuristic duration.

11. **Persistence**
   - Save final itinerary JSON (`daily_plan`) into `itineraries`.
   - Return a mobile-friendly payload with title, overview, costs, days, and location info.

### Why this is agentic
- It combines retrieval + reasoning + tool use + feedback correction loop.
- It has deterministic control around the model (guardrails before and after LLM).
- It can branch behavior (single-city vs corridor, fallback paths, terminal errors).

---

## 4.2 AI Chat Agent Workflow

Primary files:
- Route layer: `backend_scripts/api/routes/chat.py`
- Service layer: `backend_scripts/api/chat/service.py`
- Storage: `chat_sessions`, `chat_messages` through `db_helper.py`

### Step-by-step flow

1. Mobile calls `/api/chat/active-session` to resume context thread.
2. Mobile sends message to `/api/chat/send`.
3. Service resolves session:
   - Reuse provided valid session, else
   - Reuse active session for latest/linked itinerary, else
   - Create new session.
4. User message is persisted immediately.
5. Service fetches or refreshes context snapshot (TTL-based, 10 minutes):
   - User profile.
   - Itinerary summary.
   - Hazards for destination keyword.
6. Service builds model input:
   - System instruction (concise, practical, safety-first).
   - Recent conversation history (compact window).
   - Snapshot as JSON context.
   - Current user question.
7. Calls OpenAI chat completions (lower temperature).
8. Saves assistant response.
9. Updates session metadata and optional auto-title.

### Chat memory model
- Short/medium memory is not embeddings-based.
- It uses:
  - Persistent conversation history in `chat_messages`.
  - Session-level `context_snapshot` JSON in `chat_sessions`.
  - Snapshot refresh timestamp and TTL for controlled recency.

---

## 4.3 NDMA Alert AI Extraction Workflow

Primary files:
- `backend_scripts/ndma_scraper.py`
- `backend_scripts/ai_alert_extractor.py`
- `backend_scripts/ndma_poller.py`

### Step-by-step flow

1. Scraper fetches NDMA advisory listings and links.
2. For each advisory, scraper downloads/extracts PDF text.
3. Text is summarized/extractively reduced (to manage token size/timeouts).
4. AI extractor prompts OpenAI to return structured JSON alerts:
   - hazard heading, location, coords, severity, description, icon_type, etc.
5. Parser performs robust JSON recovery/cleaning (handles malformed/truncated outputs).
6. Alerts are normalized (icon/severity mapping, coordinate fallback, region inference).
7. Poller deduplicates via hashes and persists to `ndma_alerts_ai`.
8. If AI extraction fails, fallback creates simplified alert structure.

### Agentic characteristics here
- Input preprocessing + LLM extraction + parser resilience + normalization + fallback.
- This is an "information extraction agent" pipeline rather than a conversational agent.

---

## 5) Tools Used by Agents

### LLM Provider
- OpenAI Chat Completions (`OPENAI_API_KEY`, `OPENAI_MODEL`).

### Deterministic tools
- Geoapify Route Matrix for travel-time and distance matrix.
- Geoapify leg queries for per-slot transit recomputation.

### Retrieval sources
- POIs and location metadata from PostgreSQL.
- NDMA AI alerts and user hazard reports from PostgreSQL.

### Operational data sources
- NDMA website advisories and PDFs.
- Geocoding for user hazard reports (Nominatim via geopy).

---

## 6) Guardrails, Reliability, and Fallback Strategy

Raahi AI uses multi-layer guardrails:

1. **Prompt constraints**
   - Strict schema specification.
   - Rule constraints (POI usage, transit realism, safety integration, no hallucinated POI IDs).

2. **Output format enforcement**
   - JSON response_format requested for itinerary agent.
   - Parser strips markdown fences if needed.

3. **Schema validation**
   - Required keys checked.
   - Type normalization and defaults for malformed fields.

4. **ID integrity checks**
   - Unknown `poi_id` values are cleared to `null`.

5. **Tool-based correction**
   - Transit legs recomputed from coordinates rather than trusting model guesses.

6. **Fallback paths**
   - Itinerary route can fall back from agent to legacy generator on non-terminal failures.
   - NDMA extraction falls back from AI extraction to heuristic/basic alert creation.
   - Routing falls back to haversine travel estimates if API tool fails.

---

## 7) Data Model for Agentic Features

### Chat persistence
- `chat_sessions`: per-thread state, snapshot JSON, last_message timestamps, archive flag.
- `chat_messages`: ordered role/content history.
- Resume optimization index migration:
  - `database/postgresql/migrations/add_chat_session_resume_index.sql`

### Itinerary persistence
- `itineraries.daily_plan` stores generated day/slot structure.
- Linked to users and used as anchor context for chat sessions.

### Hazard intelligence
- `ndma_alerts_ai`: AI-extracted NDMA advisories with severity, coords, source, hash, activity status.
- `hazard_reports`: user-submitted hazards.

### Emergency support
- `itinerary_emergency_contacts`: per-itinerary emergency contacts.
- `safe_points`: hospital/police/fuel/workshop locations for emergency modules.

---

## 8) Mobile App Integration with Agentic Backend

### AI Chat module
- API client: `mobile_app/lib/features/ai_chat/api_service.dart`
- Calls:
  - `GET /api/chat/active-session`
  - `POST /api/chat/send`
  - `GET /api/chat/sessions`
  - `GET /api/chat/sessions/{id}/messages`

### Itinerary module
- API client: `mobile_app/lib/features/itinerary/api_service.dart`
- Calls:
  - `POST /api/itinerary/recommend`
  - `POST /api/itinerary/generate`
- Client parser supports both new RAG/agent schema and legacy schema for backward compatibility.

### Hazard / Risk modules
- Consume NDMA + user hazards from backend endpoints.
- Nearby hazard checks (`/api/hazards/nearby`) support route safety awareness.

### Emergency module
- Safe points and emergency contacts integrate with non-LLM safety workflows.

---

## 9) Environment and Runtime Configuration

Reference: `.env.example`

Important variables:
- `OPENAI_API_KEY`, `OPENAI_MODEL`
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- `GEOAPIFY_API_KEY`
- Optional pipeline selector (`POI_ENRICHER=openai|ollama`)

Notes:
- If OpenAI key is missing, AI modules that require it cannot initialize.
- Itinerary route has legacy fallback path.
- Mobile currently uses a hardcoded ngrok base URL in API service files, so deployment should centralize base URL config.

---

## 10) Testing and Evaluation Status

AI-related tests currently present:
- `backend_scripts/unit_test_cases/itnerary_test_cases.py`
  - Budget rejection scenarios.
  - Unknown-city terminal handling.
  - NDMA query validity.
  - Hazard retrieval list behavior.

Current testing gaps (good to discuss in FYP defense):
- Limited automated mocking of LLM responses.
- Limited formal regression tests for prompt/schema drift.
- Limited load/performance testing under API failures or tool outages.

---

## 11) Strengths and Limitations of Current Agentic Design

### Strengths
- Clear orchestrator architecture with deterministic control around the LLM.
- Strong real-world grounding via DB retrieval + route matrix tool.
- Good safety context integration via NDMA and hazard reports.
- Robust fallback behavior in major critical paths.
- Persistent chat memory tied to itinerary lifecycle.

### Limitations
- No semantic/vector memory for chat; mostly session + snapshot strategy.
- No true function-calling loop inside model call (tooling is orchestrated externally).
- Prompt/output quality depends on retrieval coverage and external API reliability.
- Hardcoded mobile base URLs reduce portability.

---

## 12) How to Explain the Agentic AI in Viva / Presentation

Use this framing:

1. **"Our AI is not just a chatbot; it is an orchestrated agent pipeline."**
2. **"The itinerary agent works in stages: retrieve -> rank -> route tool -> LLM -> validate -> correct -> persist."**
3. **"We combine deterministic logic with generative reasoning to improve reliability."**
4. **"Safety is integrated by feeding NDMA and hazard context into both itinerary and chat."**
5. **"We built fallback paths so the system degrades gracefully when AI/tools fail."**

You can present it as three agents:
- **Planning Agent** (ItineraryAgent)
- **Conversation Agent** (ChatService with contextual memory)
- **Alert Extraction Agent** (NDMA PDF to structured hazards)

---

## 13) Future Improvements (High-Value Roadmap)

1. Add evaluation harness with golden prompts/outputs and schema compliance scoring.
2. Add semantic retrieval/memory (vector store) for long-horizon chat personalization.
3. Add explicit tool-call planner loop (ReAct/function-calling style) for itinerary decisions.
4. Add model/provider fallback chain (OpenAI -> local model -> safe template output).
5. Externalize mobile/backend base URLs by environment per platform.
6. Add observability for token usage, latency, and failure categories across agent stages.

---

## 14) One-Paragraph FYP Thesis Summary

Raahi AI demonstrates an applied Agentic AI architecture for travel and safety: a mobile-first platform where Python orchestrators combine structured retrieval, deterministic ranking heuristics, external routing tools, and LLM generation to produce realistic itineraries and context-aware safety guidance. The system persists state in PostgreSQL (itineraries, chat sessions/messages, NDMA and user hazards), enriches real-world advisories through AI extraction pipelines, and applies post-generation validation/fallback mechanisms to improve reliability. This hybrid design shows how practical agentic workflows can outperform isolated LLM prompts in real product scenarios.

