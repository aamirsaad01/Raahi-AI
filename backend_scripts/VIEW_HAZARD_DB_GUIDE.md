# 📊 Viewing Hazard Alerts in Database

## Quick Method: Use Python Script

```bash
cd backend_scripts
python view_hazard_alerts.py
```

This shows:
- All NDMA alerts
- All user-reported hazards
- Statistics by severity
- Recent activity

---

## Direct SQL Queries (pgAdmin or psql)

### View All NDMA Alerts

```sql
SELECT 
    alert_id,
    title,
    published_date,
    advisory_type,
    severity,
    affected_regions,
    scraped_at,
    is_active
FROM ndma_alerts
WHERE is_active = TRUE
ORDER BY scraped_at DESC;
```

### View All User-Reported Hazards

```sql
SELECT 
    hazard_id,
    title,
    description,
    severity,
    location,
    reported_at,
    user_id
FROM hazard_reports
ORDER BY reported_at DESC;
```

### Count Alerts

```sql
-- Total NDMA alerts
SELECT COUNT(*) FROM ndma_alerts WHERE is_active = TRUE;

-- Total user reports
SELECT COUNT(*) FROM hazard_reports;

-- By severity
SELECT severity, COUNT(*) 
FROM ndma_alerts 
WHERE is_active = TRUE
GROUP BY severity;
```

### View Recent Alerts (Last 7 days)

```sql
SELECT title, severity, scraped_at
FROM ndma_alerts
WHERE scraped_at >= NOW() - INTERVAL '7 days'
ORDER BY scraped_at DESC;
```

### View Specific Alert Details

```sql
SELECT *
FROM ndma_alerts
WHERE alert_id = 1;  -- Replace with your alert ID
```

### View Alerts by Type

```sql
SELECT advisory_type, COUNT(*) as count
FROM ndma_alerts
WHERE is_active = TRUE
GROUP BY advisory_type
ORDER BY count DESC;
```

### View Alerts by Region

```sql
SELECT 
    unnest(affected_regions) as region,
    COUNT(*) as count
FROM ndma_alerts
WHERE is_active = TRUE
GROUP BY region
ORDER BY count DESC;
```

---

## Using pgAdmin

1. Open **pgAdmin 4**
2. Connect to your PostgreSQL server
3. Navigate to: **Databases → raahi_ai → Schemas → public → Tables**
4. Right-click on `ndma_alerts` → **View/Edit Data → All Rows**
5. Or use **Query Tool** to run SQL queries

---

## Using psql (Command Line)

```bash
psql -U postgres -d raahi_ai

# Then run queries:
SELECT * FROM ndma_alerts WHERE is_active = TRUE;
\q  # to exit
```

---

## Quick Stats Query

```sql
-- Complete overview
SELECT 
    'NDMA Alerts' as source,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE severity = 'critical') as critical,
    COUNT(*) FILTER (WHERE severity = 'high') as high,
    COUNT(*) FILTER (WHERE severity = 'medium') as medium,
    COUNT(*) FILTER (WHERE severity = 'low') as low
FROM ndma_alerts
WHERE is_active = TRUE

UNION ALL

SELECT 
    'User Reports' as source,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE severity = 'critical') as critical,
    COUNT(*) FILTER (WHERE severity = 'high') as high,
    COUNT(*) FILTER (WHERE severity = 'medium') as medium,
    COUNT(*) FILTER (WHERE severity = 'low') as low
FROM hazard_reports;
```

---

## Export to CSV

```sql
-- In psql:
\copy (SELECT * FROM ndma_alerts WHERE is_active = TRUE) TO 'ndma_alerts.csv' CSV HEADER;
```

---

## Current Database Status

Based on the last run:
- **10 NDMA alerts** (9 new + 1 old)
- **0 user reports**
- **1 High severity** alert
- **9 Low severity** alerts


