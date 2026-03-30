# 🤖 AI-Powered Alert Extraction Setup

## Overview

The NDMA scraper now uses **Google Gemini AI** to extract structured hazard alerts from PDF advisories. This provides much better accuracy and structured data extraction.

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend_scripts
pip install -r requirements.txt
```

This will install:
- `google-generativeai==0.8.3` - Google Gemini AI library
- `pdfplumber==0.11.0` - PDF text extraction
- `PyPDF2==3.0.1` - PDF parsing fallback

### 2. Get Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key

### 3. Add API Key to .env

Add this line to your `.env` file in the repository root:

```env
GEMINI_API_KEY=your_api_key_here
```

### 4. Create Database Table

Run the migration script to create the new AI-extracted alerts table:

```bash
# Using psql
psql -U postgres -d raahi_ai -f database/postgresql/update_ndma_alerts_ai_schema.sql

# Or using pgAdmin
# Open Query Tool and execute the contents of update_ndma_alerts_ai_schema.sql
```

## How It Works

1. **Scraper finds PDF advisory** → Downloads PDF
2. **Extracts PDF text** → Uses pdfplumber to get all text
3. **Sends to Gemini AI** → AI analyzes PDF content
4. **AI extracts structured alerts** → Returns JSON with:
   - Heading (e.g., "Snowfall", "Flood")
   - Location name with coordinates
   - Severity (low/medium/high/critical)
   - Description
   - Icon type and color code
   - Affected regions
5. **Saves to database** → Stores in `ndma_alerts_ai` table

## Database Schema

The new `ndma_alerts_ai` table stores:

| Field | Type | Description |
|-------|------|-------------|
| `heading` | VARCHAR | Alert type (Snowfall, Flood, etc.) |
| `location_name` | VARCHAR | Specific location (Gilgit, Naran, etc.) |
| `latitude` | DECIMAL | Location latitude |
| `longitude` | DECIMAL | Location longitude |
| `severity` | VARCHAR | low/medium/high/critical |
| `icon_type` | VARCHAR | snowfall/flood/landslide/etc. |
| `color_code` | VARCHAR | red/yellow/green (for severity) |
| `description` | TEXT | Brief description for detail sheet |
| `source` | VARCHAR | NDMA/PMD/Crowd-Sourced |
| `ai_extracted` | BOOLEAN | Whether extracted by AI |
| `extraction_confidence` | DECIMAL | AI confidence score (0.0-1.0) |

## Testing

### Test AI Extraction

```bash
python backend_scripts/ndma_poller.py --once
```

You should see:
```
🤖 Extracting alerts from PDF using AI...
✅ AI extracted 3 alert(s) from PDF
✅ Saved 3 new AI-extracted alerts to database
```

### View Extracted Alerts

```bash
python backend_scripts/view_hazard_alerts.py
```

## Benefits

✅ **Accurate Extraction** - AI understands context better than regex
✅ **Structured Data** - Consistent format with all required fields
✅ **Multiple Hazards** - Can extract multiple alerts from one PDF
✅ **Coordinates** - Automatically includes location coordinates
✅ **Icon & Color** - Pre-determined based on severity and type
✅ **Better Descriptions** - AI-generated concise descriptions

## API Changes

The `/api/hazards` endpoint now returns AI-extracted alerts with:
- Proper coordinates (latitude/longitude)
- Structured heading and description
- Icon type and color code
- Source information

## Troubleshooting

### "GEMINI_API_KEY not found"
- Make sure you added `GEMINI_API_KEY=...` to your `.env` file
- Restart the API server after adding the key

### "ndma_alerts_ai table not found"
- Run the migration script: `database/postgresql/update_ndma_alerts_ai_schema.sql`

### "AI extraction returned no alerts"
- Check if PDF content is being extracted correctly
- Verify API key is valid
- Check logs for AI response errors

### Rate Limits
- Gemini free tier has rate limits
- If you hit limits, the scraper will log warnings
- Consider upgrading to paid tier for production

## Cost

- **Gemini 1.5 Flash** (used here) is **FREE** for reasonable usage
- No credit card required
- Suitable for development and moderate production use

