# 🚀 Groq API Setup for POI Enrichment

## Overview

The POI enrichment system now uses **Llama 3.1 70B via Groq** instead of Gemini, providing:
- ✅ **14,400 requests/day** (vs Gemini's 20/day)
- ✅ **High accuracy** (comparable to GPT-3.5)
- ✅ **Fast inference** (Groq's optimized hardware)
- ✅ **Free tier** with generous limits

---

## Setup Instructions

### 1. Get Groq API Key (FREE)

1. Go to [Groq Console](https://console.groq.com/keys)
2. Sign up with your Google/GitHub account (free)
3. Click "Create API Key"
4. Copy your API key

### 2. Add API Key to .env

Add this line to your `.env` file in the repository root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

**Note:** You can keep `GEMINI_API_KEY` if you're still using it for hazard alerts, but POI enrichment now uses Groq.

### 3. Install Dependencies

```bash
cd backend_scripts
python -m pip install groq
```

Or install all requirements:

```bash
python -m pip install -r requirements.txt
```

---

## Test the Setup

```bash
cd backend_scripts/api_collectors
python llm_enricher.py
```

**Expected output:**
```
✅ LLM Enricher initialized with Llama 3 via Groq
✅ Enriched: Fairy Meadows

Description: Fairy Meadows is a stunning alpine meadow...
Rating: 4.8/5.0
Cost: High (5000-12000 PKR)
...
```

---

## Model Details

- **Model:** `llama-3.1-70b-versatile`
- **Provider:** Groq (optimized inference)
- **Free Tier:** 14,400 requests/day
- **Speed:** Very fast (optimized hardware)
- **Accuracy:** High (comparable to GPT-3.5)

---

## Rate Limits

| Tier | Requests/Day | Notes |
|------|--------------|-------|
| Free | 14,400 | Per model, resets daily |
| Paid | Higher | Contact Groq for details |

**For POI Collection:**
- With 138 locations and ~10 POIs per location = ~1,380 POIs
- At 14,400 requests/day, you can collect all POIs in one day! ✅

---

## Troubleshooting

### "Groq API key not found"
- Make sure `GROQ_API_KEY` is in your `.env` file
- Restart your terminal/IDE after adding the key

### "ModuleNotFoundError: No module named 'groq'"
```bash
python -m pip install groq==0.11.1
```

### Rate Limit Errors
- Free tier: 14,400 requests/day
- Wait 24 hours for reset, or upgrade to paid tier

---

## Migration from Gemini

If you were using Gemini before:
1. ✅ Code updated automatically - no changes needed
2. ✅ Just add `GROQ_API_KEY` to `.env`
3. ✅ Install `groq` package
4. ✅ Re-run POI collection pipeline

The old `GEMINI_API_KEY` can remain in `.env` if you're still using Gemini for hazard alerts.

---

## Next Steps

After setup:
1. Empty POIs table: `python empty_pois_table.py`
2. Re-collect POIs: `python poi_pipeline.py`
3. All POIs will be enriched with Llama 3 via Groq! 🎉

