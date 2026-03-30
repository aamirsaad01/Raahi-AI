# 🚀 Ollama Setup for POI Enrichment

## Overview

The POI enrichment system now uses **Ollama** (local, unlimited) instead of cloud APIs, providing:
- ✅ **No API limits** - runs completely locally
- ✅ **No API keys needed** - completely free
- ✅ **High accuracy** - using Llama 3.2
- ✅ **Privacy** - all data stays on your machine
- ✅ **Offline capable** - works without internet

---

## Setup Instructions

### Step 1: Install Ollama

**Windows:**
1. Download from: https://ollama.com/download/windows
2. Run the installer
3. Ollama will start automatically

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Step 2: Pull the Model

Open a terminal and run:

```bash
ollama pull llama3.2
```

This downloads the Llama 3.2 model (~2GB). It may take a few minutes.

**Alternative models** (if you want different ones):
- `llama3.1` - Llama 3.1 (larger, more accurate)
- `llama3` - Llama 3 (older version)
- `mistral` - Mistral model
- `gemma2` - Google Gemma 2

### Step 3: Verify Installation

Test that Ollama is running:

```bash
ollama list
```

You should see `llama3.2` in the list.

Test the API:

```bash
ollama run llama3.2 "Hello, world!"
```

### Step 4: Test POI Enricher

```bash
cd backend_scripts/api_collectors
python llm_enricher.py
```

**Expected output:**
```
✅ LLM Enricher initialized with Ollama (model: llama3.2)
✅ Enriched: Fairy Meadows
...
```

---

## Configuration (Optional)

You can customize Ollama settings in your `.env` file:

```env
# Ollama configuration (optional)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

**Default values:**
- `OLLAMA_BASE_URL`: `http://localhost:11434` (Ollama's default)
- `OLLAMA_MODEL`: `llama3.2`

---

## Model Details

- **Model:** `llama3.2` (default)
- **Provider:** Ollama (local)
- **Limits:** None (unlimited!)
- **Speed:** Depends on your hardware (GPU recommended)
- **Accuracy:** High (comparable to GPT-3.5)
- **Size:** ~2GB download

---

## Performance Tips

### For Faster Processing:

1. **Use GPU** (if available):
   - Ollama automatically uses GPU if available
   - Much faster than CPU-only

2. **Use Smaller Model** (if speed is priority):
   ```bash
   ollama pull llama3.2:1b  # 1B parameter version (faster)
   ```
   Then set `OLLAMA_MODEL=llama3.2:1b` in `.env`

3. **Use Larger Model** (if accuracy is priority):
   ```bash
   ollama pull llama3.1  # Larger, more accurate
   ```
   Then set `OLLAMA_MODEL=llama3.1` in `.env`

---

## Troubleshooting

### "Cannot connect to Ollama"
- Make sure Ollama is running: `ollama list` should work
- Check if port 11434 is available
- Restart Ollama service if needed

### "Model not found"
- Pull the model: `ollama pull llama3.2`
- Check available models: `ollama list`
- Verify model name in `.env` matches

### Slow Processing
- Use GPU if available (Ollama auto-detects)
- Try smaller model: `llama3.2:1b`
- Close other applications to free up resources

### Out of Memory
- Use smaller model: `llama3.2:1b`
- Close other applications
- Reduce batch size in pipeline

---

## Advantages Over Cloud APIs

| Feature | Ollama | Groq/Gemini |
|---------|--------|-------------|
| **Limits** | None | Daily limits |
| **Cost** | Free | Free (with limits) |
| **Privacy** | 100% local | Data sent to cloud |
| **Internet** | Not required | Required |
| **Speed** | Depends on hardware | Fast (cloud) |
| **Setup** | Requires installation | Just API key |

---

## Next Steps

After setup:
1. Empty POIs table: `python empty_pois_table.py`
2. Re-collect POIs: `python poi_pipeline.py`
3. All POIs will be enriched locally with no limits! 🎉

---

## Useful Commands

```bash
# List installed models
ollama list

# Pull a new model
ollama pull llama3.2

# Remove a model
ollama rm llama3.2

# Run a quick test
ollama run llama3.2 "What is Pakistan?"

# Check Ollama status
curl http://localhost:11434/api/tags
```

