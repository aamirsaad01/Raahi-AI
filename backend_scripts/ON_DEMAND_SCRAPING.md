# 🔄 On-Demand NDMA Scraping

## How It Works

The NDMA scraper now runs automatically in two scenarios:

1. **When API starts** - Scrapes once on startup (in background thread)
2. **When user refreshes** - Scrapes when refresh button is pressed in Flutter app

## Implementation

### Backend (api.py)

- ✅ **Startup Scraping**: Runs automatically when `api.py` starts
- ✅ **Manual Refresh Endpoint**: `POST /api/hazards/refresh`
- ✅ **Background Thread**: Doesn't block API startup

### Frontend (Flutter)

- ✅ **Refresh Button**: Triggers scraper + reloads hazards
- ✅ **Pull-to-Refresh**: Also triggers scraper
- ✅ **User Feedback**: Shows snackbar with new alerts count

## API Endpoint

### Refresh Hazards

```
POST /api/hazards/refresh
```

**Response:**
```json
{
  "success": true,
  "message": "Hazards refreshed successfully",
  "advisories_found": 9,
  "new_advisories": 2,
  "duration_seconds": 3.45
}
```

## Usage

### Starting the API

```bash
cd backend_scripts
python api.py
```

**What happens:**
1. API server starts
2. NDMA scraper runs automatically in background
3. New advisories are saved to database
4. API is ready to serve requests

### User Refreshing in App

When user presses refresh button:
1. Flutter app calls `/api/hazards/refresh`
2. Backend scrapes NDMA website
3. New advisories saved to database
4. Flutter app reloads hazards from database
5. User sees updated list

## Benefits

✅ **No manual intervention** - Runs automatically
✅ **On-demand updates** - Fresh data when needed
✅ **Efficient** - Only scrapes when API starts or user requests
✅ **User control** - Users can refresh anytime
✅ **Non-blocking** - Doesn't slow down API startup

## Testing

### Test Startup Scraping

1. Start API: `python api.py`
2. Check logs - should see: "🔄 Running NDMA scraper on API startup..."
3. Check database: `python view_hazard_alerts.py`

### Test Manual Refresh

1. Start API: `python api.py`
2. Open Flutter app
3. Go to Hazard Map
4. Press refresh button
5. Should see snackbar with new alerts count

### Test API Endpoint Directly

```bash
curl -X POST http://127.0.0.1:5000/api/hazards/refresh
```

## Logs

You'll see logs like:
```
INFO:__main__:🔄 Running NDMA scraper on API startup...
INFO:__main__:📡 Scraping NDMA advisories...
INFO:__main__:✅ Startup scrape: 2 new advisories
```

Or when manually triggered:
```
INFO:__main__:🔄 Manual refresh triggered from Flutter app
INFO:__main__:📋 Found 9 advisories
INFO:__main__:✅ Saved 2 new advisories to database
```

## Notes

- Startup scraping runs in a background thread (non-blocking)
- Duplicate detection prevents saving the same alert twice
- If scraper fails, API still starts normally
- Manual refresh shows user-friendly error messages if it fails

