# 🚀 POI Collection System - Usage Guide

Complete guide to collecting and enriching POI (Points of Interest) data for your itinerary generator.

---

## 📋 Prerequisites

Before you start, make sure you have:

- [x] PostgreSQL database running with `raahi_ai` database
- [x] Database schema updated (run `database/postgresql/db_init.sql`)
- [x] Location data loaded (138 locations in `location_mapping` table)
- [x] **OpenAI API key** in `.env` as `OPENAI_API_KEY` (recommended for enrichment), **or** local **Ollama** if you set `POI_ENRICHER=ollama`
- [x] Python dependencies installed (`pip install -r requirements.txt` includes `openai`)
- [x] `.env` file created with credentials (see root `.env.example`)

### Full repopulation (wipe + OSM + enrichment)

From the repo root:

```bash
python backend_scripts/api_collectors/repopulate_pois.py --yes
```

Or wipe only, then run the pipeline with `--force`:

```bash
python backend_scripts/api_collectors/empty_pois_table.py --yes
cd backend_scripts/api_collectors
python poi_pipeline.py --force
```

---

## 🔧 Setup (One-Time)

### 1. Install Dependencies

```bash
cd backend_scripts
pip install -r requirements.txt
```

This installs:
- OpenStreetMap (Overpass) usage via `requests` (free)
- **openai** (POI text enrichment when `OPENAI_API_KEY` is set)
- Unsplash client (optional photos)

### 2. Update Database Schema

If you haven't already, add the POI table:

```bash
# Option 1: Using pgAdmin
# Open pgAdmin → Query Tool → Run database/postgresql/db_init.sql

# Option 2: Using psql
psql -U postgres -d raahi_ai -f database/postgresql/db_init.sql
```

### 3. Test Your Setup

```bash
cd backend_scripts
python test_poi_system.py
```

You should see all essential tests passing:
```
✅ ALL ESSENTIAL TESTS PASSED!
🚀 You're ready to collect POI data!
```

---

## 🎯 Collecting POI Data

### Quick Start: Test with 3 Locations

Start small to verify everything works:

```bash
cd backend_scripts/api_collectors
python poi_pipeline.py --limit 3
```

**What this does:**
1. Fetches first 3 locations from your database
2. For each location, queries OpenStreetMap for tourist attractions
3. Enriches each POI with **OpenAI** (or Ollama if no API key / `POI_ENRICHER=ollama`)
4. Optionally fetches photos from Unsplash
5. Saves everything to `points_of_interest` table

**Expected output:**
```
🚀 STARTING PIPELINE: Processing 3 locations
📍 [1/3] Processing: Gilgit, Gilgit-Baltistan
🌍 Querying OSM for POIs...
✅ Found 8 POIs from OSM
🤖 Enriching POIs with LLM...
✅ Saved: Gilgit Fort
...
🎉 PIPELINE COMPLETE!
```

**Time:** ~5-10 minutes for 3 locations (depending on POI count)

---

### Full Collection: All 138 Locations

Once you've verified it works, run the full collection:

```bash
cd backend_scripts/api_collectors
python poi_pipeline.py
```

**What to expect:**
- **Time:** 3-6 hours (depending on POI density)
- **Total POIs:** ~500-1000 (estimate)
- **Rate limiting:** Built-in delays to respect API limits
- **Resumable:** If interrupted, re-run - it skips already processed locations

**Monitor progress:**
The script shows real-time progress:
```
📍 [47/138] Processing: Hunza, Gilgit-Baltistan
   [3/12] Processing: Attabad Lake
   ✅ Saved: Attabad Lake
```

---

## 📊 Check Your Data

### View Statistics

```bash
cd backend_scripts/api_collectors
python poi_pipeline.py --stats
```

**Output:**
```
📊 POI DATABASE STATISTICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total POIs: 847
Average Rating: 4.2/5.0

POIs by Category:
  nature         : 512
  cultural       :  98
  adventure      :  87
  religious      :  76
  historical     :  74

POIs by Region:
  Gilgit-Baltistan    : 412
  KPK Highlands       : 198
  Hazara Division     : 156
  Murree & Galyat     :  81
```

---

## 🎨 What Data You Get

For each POI, the system collects:

### From OpenStreetMap (Free):
- ✅ Name
- ✅ Coordinates (latitude, longitude)
- ✅ Basic category (tourism, natural, etc.)
- ✅ Initial activity tags

### From Gemini LLM (Free):
- ✅ **Description** (2-3 engaging sentences)
- ✅ **Rating** (1-5, estimated based on popularity)
- ✅ **Category** (nature, cultural, adventure, religious, historical)
- ✅ **Difficulty** (easy, moderate, hard, extreme)
- ✅ **Activities** (hiking, photography, camping, etc.)
- ✅ **Mood Tags** (adventurous, relaxed, romantic, family, cultural)
- ✅ **Cost Estimate** (Low/Medium/High + PKR range)
- ✅ **Best Months** to visit
- ✅ **Duration** (average hours to spend)
- ✅ **Accessibility** (road conditions, vehicle needs)
- ✅ **Permits** required or not
- ✅ **Highlights** (3-4 key features)
- ✅ **Nearby Facilities** (hotels, food, fuel)

### From Unsplash (Optional):
- ✅ Photos (up to 3 per POI)
- ✅ Photographer attribution

---

## 🔄 Advanced Usage

### Resume from Specific Location

If the pipeline was interrupted:

```bash
# Skip first 50 locations
python poi_pipeline.py --skip 50

# Process next 10 locations
python poi_pipeline.py --skip 50 --limit 10
```

### Re-process Specific Regions

To update data for specific locations, delete their POIs first:

```sql
-- In pgAdmin Query Tool:
DELETE FROM points_of_interest 
WHERE location_id IN (
    SELECT location_id FROM location_mapping 
    WHERE parent_region = 'Gilgit-Baltistan'
);
```

Then re-run:
```bash
python poi_pipeline.py
```

---

## 🧪 Testing Individual Components

### Test OSM Collector Only

```bash
cd backend_scripts/api_collectors
python osm_collector.py
```

### Test LLM Enricher Only

```bash
python llm_enricher.py
```

### Test Photo Fetcher Only

```bash
python photo_fetcher.py
```

---

## 📝 Database Queries

### View Sample POIs

```sql
-- Top rated POIs
SELECT name, rating, category, estimated_cost 
FROM points_of_interest 
ORDER BY rating DESC 
LIMIT 10;

-- POIs for specific location
SELECT poi.name, poi.category, poi.rating, poi.activities
FROM points_of_interest poi
JOIN location_mapping loc ON poi.location_id = loc.location_id
WHERE loc.city = 'Hunza';

-- POIs by mood tag
SELECT name, mood_tags, rating
FROM points_of_interest
WHERE mood_tags @> '["adventurous"]'::jsonb
ORDER BY rating DESC;
```

---

## ⚡ Performance & Costs

### API Limits (All FREE tiers):

| API | Free Limit | Our Usage | Status |
|-----|------------|-----------|--------|
| **OSM Overpass** | Unlimited | ~5-10 requests/location | ✅ Safe |
| **Google Gemini** | 60 req/min | ~1-2 req/sec | ✅ Safe |
| **Unsplash** | 50 req/hour | Optional | ✅ Safe |

**Built-in Rate Limiting:**
- 1 second delay between POIs
- 2 second delay between locations
- Respects all API limits

**Cost Breakdown:**
```
OSM Overpass: $0.00 (unlimited free)
Gemini API:   $0.00 (free tier)
Unsplash:     $0.00 (free tier)
─────────────────────────────
TOTAL:        $0.00 ✅
```

---

## 🐛 Troubleshooting

### "No module named 'google.generativeai'"

```bash
cd backend_scripts
pip install -r requirements.txt
```

### "Gemini API key not found"

Check your `.env` file exists in project root (`E:\Raahi-AI\.env`)

### "Database connection failed"

1. Make sure PostgreSQL is running
2. Verify credentials in `.env`
3. Test with: `python database/postgresql/connection.py`

### "No POIs found for location"

This is normal for some remote locations. OSM data varies by region.

### Pipeline is slow

This is normal! LLM enrichment takes time (~2-3 seconds per POI). For 1000 POIs, expect 3-6 hours.

---

## 📊 Expected Results

After full collection (138 locations):

- **Total POIs:** 500-1,200 (varies by OSM data)
- **Coverage:** All major tourist attractions in Northern Pakistan
- **Quality:** LLM-generated content is surprisingly accurate
- **Photos:** 30-60% coverage (depends on Unsplash database)

**Data Quality:**
- ✅ Names & Coordinates: Highly accurate (from OSM)
- ✅ Descriptions: Good quality (LLM-generated)
- ✅ Ratings: Reasonable estimates (LLM-based)
- ✅ Costs: Realistic for Pakistan tourism
- ⚠️  Photos: May not always match exact location

---

## 🎯 Next Steps: Using POI Data for Itineraries

Once you have POI data, you can:

1. **Query by Mood:**
```python
# Get adventurous POIs in Gilgit-Baltistan
pois = db.query("""
    SELECT * FROM points_of_interest 
    WHERE mood_tags @> '["adventurous"]'
    AND location_id IN (
        SELECT location_id FROM location_mapping 
        WHERE parent_region = 'Gilgit-Baltistan'
    )
    ORDER BY rating DESC
""")
```

2. **Filter by Budget:**
```python
# Get low-cost POIs
pois = db.query("""
    SELECT * FROM points_of_interest 
    WHERE estimated_cost = 'Low'
    AND estimated_cost_pkr_max < 3000
""")
```

3. **Match Activities:**
```python
# Get hiking spots
pois = db.query("""
    SELECT * FROM points_of_interest 
    WHERE activities @> '["hiking"]'::jsonb
""")
```

4. **Build Itinerary Algorithm:**
```python
def generate_itinerary(user_prefs):
    # Match user mood → filter POIs by mood_tags
    # Match user budget → filter by cost range
    # Match user activities → filter by activities
    # Sort by rating
    # Calculate daily schedules based on duration
    # Return day-by-day plan
```

---

## 📚 File Reference

```
backend_scripts/
├── api_collectors/
│   ├── osm_collector.py      # Fetch POIs from OpenStreetMap
│   ├── llm_enricher.py       # Enrich with Gemini LLM
│   ├── photo_fetcher.py      # Fetch photos from Unsplash
│   └── poi_pipeline.py       # Main orchestrator
├── test_poi_system.py        # Test all components
├── CREDENTIALS_SETUP.md      # How to get API keys
└── POI_COLLECTION_GUIDE.md   # This file!
```

---

## 🎉 Ready to Start!

```bash
# 1. Test your setup
python test_poi_system.py

# 2. Try 3 locations
cd api_collectors
python poi_pipeline.py --limit 3

# 3. Check results
python poi_pipeline.py --stats

# 4. If all looks good, run full collection
python poi_pipeline.py
```

**Happy collecting! 🚀**

