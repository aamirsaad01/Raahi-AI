# Raahi-AI

## 🗄️ Database Setup (PostgreSQL)

For detailed database setup instructions, see [`database/README.md`](database/README.md).

### Quick Start:
1. **Create Database:** Open pgAdmin → Create database named `raahi_ai`
2. **Run Schema:** Execute `database/postgresql/db_init.sql` in pgAdmin Query Tool
3. **Environment Setup:** Copy `.env.example` to `.env` and fill your credentials
4. **Install Dependencies:** `pip install -r database/requirements.txt`
5. **Test Connection:** `python database/postgresql/connection.py`

### Connection URL Format:
```
postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

Example: `postgresql://postgres:password@localhost:5432/raahi_ai`