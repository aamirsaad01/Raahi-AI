# 🧪 Testing the NDMA Poller Module

## Prerequisites Checklist

- [ ] PostgreSQL database `raahi_ai` is created
- [ ] `.env` file exists in repository root with database credentials
- [ ] Python dependencies installed (`pip install -r backend_scripts/requirements.txt`)

## Step-by-Step Testing Guide

### Step 1: Verify Database Connection

First, make sure you can connect to your database:

```bash
python database/postgresql/connection.py
```

Expected output:
```
✅ Connected to PostgreSQL successfully!
📅 Server Time: [current timestamp]
```

If this fails, check your `.env` file.

---

### Step 2: Create the NDMA Alerts Table

**Option A: Using psql (Command Line)**
```bash
psql -U postgres -d raahi_ai -f database/postgresql/add_ndma_alerts_table.sql
```

**Option B: Using pgAdmin**
1. Open pgAdmin 4
2. Connect to your PostgreSQL server
3. Right-click on `raahi_ai` database → **Query Tool**
4. Open `database/postgresql/add_ndma_alerts_table.sql`
5. Click **Execute (▶)** or press F5

**Verify table was created:**
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_name = 'ndma_alerts';
```

Should return: `ndma_alerts`

---

### Step 3: Test the Scraper (No Database Required)

This tests if we can successfully scrape the NDMA website:

```bash
cd backend_scripts
python ndma_scraper.py
```

**Expected output:**
```
🧪 Testing NDMA Scraper
============================================================

📡 Fetching http://www.ndma.gov.pk/advisories...
📋 Found X advisories

✅ Found X advisories

1. [Advisory Title]
   Type: [Advisory Type]
   Date: [Date]
   Severity: [low/medium/high/critical]
   Regions: [Affected regions]
   URL: [Advisory URL]
...
```

**What to check:**
- ✅ No errors
- ✅ At least some advisories found (even if 0, that's okay for testing)
- ✅ Advisory data looks correct

**If it fails:**
- Check internet connection
- The NDMA website might be down
- Website structure might have changed (we may need to update the scraper)

---

### Step 4: Test the Poller (Run Once)

This will scrape and save to database:

```bash
cd backend_scripts
python ndma_poller.py --once
```

**Expected output:**
```
============================================================
🔄 Starting NDMA polling cycle
============================================================
✅ ndma_alerts table exists
📡 Scraping NDMA advisories...
📋 Found X advisories
Found Y existing alerts in database
✅ Saved Z new advisories to database
============================================================
✅ Polling complete: Z new advisories saved
⏱️  Duration: X.XX seconds
============================================================
```

**What to check:**
- ✅ No errors
- ✅ "Saved X new advisories" (could be 0 if all are duplicates)
- ✅ Duration is reasonable (< 60 seconds)

---

### Step 5: Verify Data in Database

**Option A: Using psql**
```bash
psql -U postgres -d raahi_ai

# Then run these queries:
```

**Option B: Using pgAdmin**
- Open Query Tool
- Run the queries below

**Query 1: Count total alerts**
```sql
SELECT COUNT(*) as total_alerts FROM ndma_alerts;
```

**Query 2: View recent alerts**
```sql
SELECT 
    title,
    published_date,
    advisory_type,
    severity,
    affected_regions,
    scraped_at
FROM ndma_alerts
ORDER BY scraped_at DESC
LIMIT 10;
```

**Query 3: View alerts by severity**
```sql
SELECT 
    severity,
    COUNT(*) as count
FROM ndma_alerts
GROUP BY severity
ORDER BY 
    CASE severity
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
    END;
```

**Query 4: View alerts by type**
```sql
SELECT 
    advisory_type,
    COUNT(*) as count
FROM ndma_alerts
GROUP BY advisory_type
ORDER BY count DESC;
```

**Query 5: Check for duplicates (should be 0)**
```sql
SELECT alert_hash, COUNT(*) as count
FROM ndma_alerts
GROUP BY alert_hash
HAVING COUNT(*) > 1;
```

---

### Step 6: Test Continuous Polling (Optional)

Run the poller continuously to see it in action:

```bash
cd backend_scripts
python ndma_poller.py --interval 0.1
```

This runs every 6 minutes (0.1 hours) for testing. Watch the logs to see:
- Polling cycles
- New advisories being saved
- Any errors

Press `Ctrl+C` to stop.

**For production**, use default 1 hour interval:
```bash
python ndma_poller.py
```

---

## Troubleshooting

### Error: "Table does not exist"
**Solution:** Run Step 2 to create the table.

### Error: "Connection failed"
**Solution:** 
1. Check `.env` file exists in repository root
2. Verify database credentials
3. Ensure PostgreSQL is running
4. Test with `python database/postgresql/connection.py`

### Error: "No advisories found"
**Possible causes:**
- NDMA website is down
- Website structure changed
- Network issues

**Solution:**
1. Visit http://www.ndma.gov.pk/advisories manually
2. Check if the page loads
3. If structure changed, we may need to update the scraper

### Error: "Module not found"
**Solution:**
```bash
cd backend_scripts
pip install -r requirements.txt
```

### Scraper finds 0 advisories
**Possible causes:**
- Website structure is different than expected
- No advisories currently on the page

**Solution:**
1. Check the website manually
2. We may need to inspect the HTML and update the scraper
3. The scraper tries multiple parsing methods, so it should work with various structures

---

## Expected Results

After successful testing, you should have:

1. ✅ `ndma_alerts` table in database
2. ✅ Some advisories saved (if NDMA website has any)
3. ✅ No duplicate entries
4. ✅ Proper severity classification
5. ✅ Region extraction working

---

## Next Steps

Once testing is successful:

1. **Set up as a service** (see `NDMA_POLLER_README.md`)
2. **Create API endpoint** to fetch alerts for Flutter app
3. **Add notification system** for critical alerts
4. **Integrate with Flutter app** to display alerts

---

## Quick Test Script

Run this to test everything at once:

```bash
# 1. Test connection
python database/postgresql/connection.py

# 2. Test scraper
python backend_scripts/ndma_scraper.py

# 3. Test poller
python backend_scripts/ndma_poller.py --once

# 4. Check results (in psql or pgAdmin)
# SELECT COUNT(*) FROM ndma_alerts;
```



