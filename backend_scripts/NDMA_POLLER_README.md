# 🚨 NDMA Poller Service

## Overview

The NDMA Poller Service automatically scrapes disaster advisories from the National Disaster Management Authority (NDMA) Pakistan website and stores them in the database for the Raahi AI app.

**Website:** http://www.ndma.gov.pk/advisories

## Features

- ✅ Automatic web scraping of NDMA advisories
- ✅ Duplicate detection using hash-based deduplication
- ✅ Severity classification (low, medium, high, critical)
- ✅ Region extraction (identifies affected areas)
- ✅ Continuous polling (runs every hour by default)
- ✅ Full content fetching from advisory detail pages

## Setup

### 1. Database Setup

First, create the `ndma_alerts` table in your PostgreSQL database:

```bash
# Using psql
psql -U postgres -d raahi_ai -f database/postgresql/add_ndma_alerts_table.sql

# Or using pgAdmin
# Open Query Tool and execute the contents of add_ndma_alerts_table.sql
```

### 2. Install Dependencies

```bash
cd backend_scripts
pip install -r requirements.txt
```

### 3. Environment Variables

Ensure your `.env` file in the repository root contains:

```env
DB_NAME=raahi_ai
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

## Usage

### Run Once (Test)

```bash
python backend_scripts/ndma_poller.py --once
```

This will:
- Scrape the NDMA website
- Check for new advisories
- Save them to the database
- Exit

### Run Continuously (Production)

```bash
python backend_scripts/ndma_poller.py
```

This will:
- Run continuously
- Poll every 1 hour (default)
- Log all activities

### Custom Interval

```bash
# Poll every 30 minutes
python backend_scripts/ndma_poller.py --interval 0.5

# Poll every 6 hours
python backend_scripts/ndma_poller.py --interval 6
```

## Database Schema

The `ndma_alerts` table stores:

| Column | Type | Description |
|--------|------|-------------|
| `alert_id` | SERIAL | Primary key |
| `title` | VARCHAR(255) | Advisory title |
| `advisory_url` | TEXT | Link to full advisory |
| `published_date` | DATE | When advisory was published |
| `advisory_type` | VARCHAR(100) | Type (e.g., "Heatwave Advisory", "GLOF Alert") |
| `content` | TEXT | Full advisory content |
| `severity` | VARCHAR(20) | low, medium, high, critical |
| `affected_regions` | TEXT[] | Array of affected regions |
| `alert_hash` | VARCHAR(64) | Unique hash for duplicate detection |
| `scraped_at` | TIMESTAMPTZ | When we scraped this alert |
| `is_active` | BOOLEAN | Whether alert is still active |
| `created_at` | TIMESTAMPTZ | Record creation time |
| `updated_at` | TIMESTAMPTZ | Last update time |

## How It Works

1. **Scraping**: The scraper fetches the NDMA advisories page
2. **Parsing**: Extracts title, date, type, and other metadata
3. **Deduplication**: Generates hash from title + date to detect duplicates
4. **Content Fetching**: Optionally fetches full content from detail pages
5. **Severity Detection**: Analyzes keywords to determine severity
6. **Region Extraction**: Identifies affected regions from text
7. **Database Storage**: Saves only new advisories

## Severity Classification

The system automatically classifies severity based on keywords:

- **Critical**: emergency, immediate, evacuate, urgent
- **High**: warning, alert, severe, extreme, danger
- **Medium**: caution, advisory, monitor, precaution
- **Low**: Default for other advisories

## Region Detection

Automatically detects mentions of:
- Gilgit-Baltistan
- KPK Highlands / Khyber Pakhtunkhwa
- Hazara Division
- Murree & Galyat
- And other Pakistani regions

## Running as a Service

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: "Daily" or "At startup"
4. Action: Start a program
5. Program: `python`
6. Arguments: `D:\Raahi-AI\Raahi-AI\backend_scripts\ndma_poller.py`
7. Start in: `D:\Raahi-AI\Raahi-AI\backend_scripts`

### Linux (systemd)

Create `/etc/systemd/system/ndma-poller.service`:

```ini
[Unit]
Description=NDMA Poller Service
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/Raahi-AI/backend_scripts
ExecStart=/usr/bin/python3 /path/to/Raahi-AI/backend_scripts/ndma_poller.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable ndma-poller
sudo systemctl start ndma-poller
```

## Monitoring

Check logs for:
- Number of advisories found
- New advisories saved
- Errors or connection issues

## Troubleshooting

### "Table does not exist"
Run the SQL migration script first:
```bash
psql -U postgres -d raahi_ai -f database/postgresql/add_ndma_alerts_table.sql
```

### "Connection failed"
Check your `.env` file and database credentials.

### "No advisories found"
The NDMA website structure may have changed. Check the website manually and update the scraper if needed.

## Next Steps

- [ ] Add API endpoint to fetch alerts for Flutter app
- [ ] Add notification system for critical alerts
- [ ] Add location-based filtering
- [ ] Add alert expiration/archival



