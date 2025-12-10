# 🔐 Credentials Setup Guide

This guide explains how to set up all required API keys and credentials for the POI collection system.

## 📋 Quick Setup Checklist

- [ ] PostgreSQL database setup
- [ ] Google Gemini API key (REQUIRED)
- [ ] Unsplash API key (Optional)
- [ ] Create `.env` file in project root

---

## 1️⃣ Database Setup (PostgreSQL)

**Already done!** You should have PostgreSQL running with the `raahi_ai` database.

If not, see: `database/README.md`

---

## 2️⃣ Google Gemini API Key (REQUIRED) ⭐

**Why:** Used to generate POI descriptions, ratings, mood tags, costs, etc.

**Cost:** 100% FREE forever (generous free tier)

**Free Tier Limits:**
- 60 requests per minute
- 1,500 requests per day
- More than enough for your project!

### How to Get:

1. **Go to:** https://makersuite.google.com/app/apikey
2. **Sign in** with your Google account
3. **Click** "Create API Key"
4. **Copy** the key (looks like: `AIzaSyC...`)
5. **Save it** - you'll need it in Step 4

**No billing required!** Completely free.

---

## 3️⃣ Unsplash API Key (Optional) 📸

**Why:** Used to fetch real photos of POIs

**Cost:** FREE (with limits)

**Free Tier Limits:**
- 50 requests per hour
- Good enough for development

**Note:** If you skip this, the system will work fine without photos. Photos are a nice-to-have, not essential.

### How to Get:

1. **Go to:** https://unsplash.com/developers
2. **Sign up** (free account)
3. **Create a new application**
   - Name: "Raahi AI"
   - Description: "Travel planning app for Northern Pakistan"
4. **Copy** the "Access Key"
5. **Save it** for Step 4

---

## 4️⃣ Create .env File

Create a file named `.env` in your **project root** (same folder as this README):

```
E:\Raahi-AI\.env
```

### .env File Contents:

```bash
# ===============================================
# Database Configuration
# ===============================================
DB_NAME=raahi_ai
DB_USER=postgres
DB_PASSWORD=your_actual_password_here
DB_HOST=127.0.0.1
DB_PORT=5432

# ===============================================
# Google Gemini API (REQUIRED)
# ===============================================
GEMINI_API_KEY=AIzaSyC_your_actual_key_here

# ===============================================
# Unsplash API (Optional)
# ===============================================
UNSPLASH_ACCESS_KEY=your_unsplash_key_here
```

**Important:**
- Replace `your_actual_password_here` with your PostgreSQL password
- Replace `AIzaSyC_your_actual_key_here` with your Gemini API key
- Replace `your_unsplash_key_here` with your Unsplash key (or leave it blank)

---

## 5️⃣ Verify Setup

### Test Database Connection:
```bash
cd database
python postgresql/connection.py
```

Expected output:
```
✅ Connected to PostgreSQL successfully!
```

### Test Gemini API:
```bash
cd backend_scripts/api_collectors
python llm_enricher.py
```

Expected output:
```
✅ LLM Enricher initialized with Gemini
✅ Enriched: Fairy Meadows
```

### Test Photo Fetcher (Optional):
```bash
cd backend_scripts/api_collectors
python photo_fetcher.py
```

Expected output:
```
✅ Photo Fetcher initialized with Unsplash API
✅ Found 2 photos for: Hunza Valley
```

---

## ⚠️ Troubleshooting

### "No module named 'google.generativeai'"
**Solution:** Install requirements
```bash
cd backend_scripts
pip install -r requirements.txt
```

### "ValueError: Gemini API key not found"
**Solution:** 
1. Make sure `.env` file exists in project root
2. Make sure `GEMINI_API_KEY=...` is in the file
3. Restart your terminal/IDE

### "Database connection failed"
**Solution:**
1. Make sure PostgreSQL is running
2. Check your password in `.env`
3. Make sure database `raahi_ai` exists

---

## 🎯 Summary

**Required:**
- PostgreSQL database ✅ (you have this)
- Gemini API key ⭐ (get from: https://makersuite.google.com/app/apikey)

**Optional:**
- Unsplash API key 📸 (get from: https://unsplash.com/developers)

**Total Cost:** $0.00 (completely free!)

---

## 📞 Need Help?

If you're stuck:
1. Check that `.env` file is in the right location: `E:\Raahi-AI\.env`
2. Check that API keys are copied correctly (no extra spaces)
3. Make sure PostgreSQL is running

Ready to collect POI data? See: `POI_COLLECTION_GUIDE.md`

