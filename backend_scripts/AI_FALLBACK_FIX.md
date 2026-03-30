# 🔧 AI Fallback Fix

## Problem
When `GEMINI_API_KEY` is not configured, the AI extractor was returning empty lists, causing no alerts to be saved.

## Solution
Added a **fallback mechanism** that creates basic structured alerts from PDF content when AI is not available.

## What Changed

### 1. Fallback Alert Creation
- When AI extractor is not available, the system now creates basic alerts from PDF content
- Extracts: heading, location, coordinates, severity, icon type, color code, description
- Uses pattern matching and heuristics to extract information

### 2. Updated Methods
- `extract_alerts_from_pdf_ai()` - Now accepts `base_advisory` parameter for fallback
- `_create_fallback_alert()` - New method to create basic alerts
- `_extract_heading_from_title()` - Extracts alert type from title
- `_extract_location_from_content()` - Extracts location from content/title
- `_get_coordinates_for_location_fallback()` - Gets coordinates for known locations
- `_determine_icon_type_fallback()` - Determines icon type from heading

### 3. Table Check
- Updated poller to check for `ndma_alerts_ai` table instead of old `ndma_alerts` table

## How It Works

**With AI (when GEMINI_API_KEY is set):**
1. Downloads PDF
2. Sends to Gemini AI
3. AI extracts structured alerts
4. Saves to database

**Without AI (fallback):**
1. Downloads PDF
2. Extracts text content
3. Uses pattern matching to extract:
   - Heading (from title keywords)
   - Location (from content/title)
   - Coordinates (from location lookup)
   - Severity (from title/content analysis)
   - Icon type (from heading)
   - Description (first 200 chars of PDF)
4. Creates basic alert structure
5. Saves to database

## Setup

### Option 1: Use AI (Recommended)
1. Get Gemini API key from https://makersuite.google.com/app/apikey
2. Add to `.env`: `GEMINI_API_KEY=your_key_here`
3. Restart API

### Option 2: Use Fallback
- No setup needed!
- System will automatically use fallback when AI is not available
- Alerts will still be created, just with basic extraction

## Testing

Run the poller:
```bash
python backend_scripts/ndma_poller.py --once
```

You should see:
- **With AI**: "✅ AI extracted X alert(s) from PDF"
- **Without AI**: "AI extractor not available, creating basic alert from PDF content"
- **Both cases**: Alerts should be saved to database

## Notes

- Fallback alerts are less accurate than AI-extracted ones
- For best results, configure `GEMINI_API_KEY`
- Fallback still creates usable alerts with location, severity, and description
- Both methods save to the same `ndma_alerts_ai` table

