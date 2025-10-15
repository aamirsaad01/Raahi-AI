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
| `checklist` | Stores location-based packing items |

### 4️⃣ Test Connection with Python
Run this script:
```bash
python database/postgresql/connection.py
