# 🚀 Quick Start: NDMA Poller

## Step 1: Create Database Table

```bash
# Using psql
psql -U postgres -d raahi_ai -f database/postgresql/add_ndma_alerts_table.sql
```

Or in pgAdmin: Open Query Tool → Execute `add_ndma_alerts_table.sql`

## Step 2: Install Dependencies

```bash
cd backend_scripts
pip install -r requirements.txt
```

## Step 3: Test the Scraper

```bash
python backend_scripts/ndma_scraper.py
```

This will test scraping without saving to database.

## Step 4: Test the Poller (Run Once)

```bash
python backend_scripts/ndma_poller.py --once
```

This will scrape and save to database.

## Step 5: Run Continuously

```bash
python backend_scripts/ndma_poller.py
```

Runs every hour by default. Press Ctrl+C to stop.

## Check Results

```sql
-- View all alerts
SELECT title, published_date, severity, advisory_type 
FROM ndma_alerts 
ORDER BY published_date DESC;

-- Count alerts
SELECT COUNT(*) FROM ndma_alerts;

-- View recent alerts
SELECT title, published_date, severity 
FROM ndma_alerts 
WHERE is_active = TRUE 
ORDER BY scraped_at DESC 
LIMIT 10;
```



