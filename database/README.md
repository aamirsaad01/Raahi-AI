# 🗄️ Raahi AI - Database Setup

## 📘 Overview
Raahi AI uses a **hybrid database model** for structured and real-time data storage.

- **PostgreSQL** — for structured data (users, itineraries, checklists, expenses)
- **Firebase Firestore** — for real-time chat, location sharing, and group data (to be added in later iterations)

This document explains how to set up the **PostgreSQL** database for Iteration 1.

---

## ⚙️ PostgreSQL Setup Instructions

### 1️⃣ Install PostgreSQL
- Download from: [https://www.postgresql.org/download/](https://www.postgresql.org/download/)
- During setup, note your **username**, **password**, and **port (default: 5432)**.

### 2️⃣ Create Database
Open **pgAdmin 4** → right-click **Databases → Create → Database**
- **Database name:** `raahi_ai`
- **Owner:** `postgres`

### 3️⃣ Run Schema File
In pgAdmin:
- Open **Query Tool**
- Copy & paste contents of `database/postgresql/db_init.sql`
- Click **Execute (▶)**

This will create the following tables:

| Table | Purpose |
|--------|----------|
| `users` | Stores user registration data |
| `itineraries` | Stores AI-generated or user-created travel plans |
| `checklist` | Stores location-based packing items (items stored as JSONB) |
| `hazard_reports` | Stores user-reported safety hazards for locations |
| `location_mapping` | Stores city location data with coordinates, climate, and region info |

### 3️⃣ (Optional) Add NDMA Alerts Table

To enable the NDMA hazard alert system, run the additional migration:

In pgAdmin:
- Open **Query Tool**
- Copy & paste contents of `database/postgresql/add_ndma_alerts_table.sql`
- Click **Execute (▶)**

This creates the `ndma_alerts` table for storing scraped disaster advisories from NDMA Pakistan.

See `backend_scripts/NDMA_POLLER_README.md` for details on the poller service.

### 4️⃣ Environment Variables Setup
1. Copy `.env.example` from the repository root to `.env` in the same location
2. Fill in your local PostgreSQL credentials:
```bash
DB_NAME=raahi_ai
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_HOST=localhost
DB_PORT=5432
```

### 5️⃣ Install Python Dependencies
Install the required packages for database scripts:
```bash
pip install -r database/requirements.txt
```

### 6️⃣ Test Connection with Python
Run this script:
```bash
python database/postgresql/connection.py
```

Expected output:
```
✅ Connected to PostgreSQL successfully!
📅 Server Time: [current timestamp]
```

### 7️⃣ Connection URL Format (for Backend Integration)
When connecting from backend code (FastAPI, Django, etc.), use this format:
```
postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

Example:
```
postgresql://postgres:your_password@localhost:5432/raahi_ai
```

---

## 📋 Database Schema Summary

### Tables & Relationships
- **users** → **itineraries** (one-to-many)
- **itineraries** → **checklist** (one-to-many)
- **users** → **hazard_reports** (one-to-many, optional)
- **itineraries** → **hazard_reports** (one-to-many, optional)
- **ndma_alerts** (standalone) - Scraped disaster advisories from NDMA Pakistan

### Key Features
- ✅ Automatic timestamps (`created_at`, `updated_at`)
- ✅ Foreign key constraints with cascade deletes
- ✅ Indexes on frequently queried columns
- ✅ JSONB support for flexible checklist items
- ✅ Unique constraints (email, user+itinerary title)
