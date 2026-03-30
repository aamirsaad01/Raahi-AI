# 📄 PDF Scraping Implementation

## What Changed

The NDMA scraper now **reads and parses PDF content** from advisories instead of just HTML metadata.

## Features

✅ **PDF Download & Parsing**
- Extracts actual PDF URLs from `secure-viewer` links
- Downloads PDFs automatically
- Extracts text content using `pdfplumber` (with `PyPDF2` fallback)

✅ **Multiple Hazard Detection**
- Detects multiple hazards in a single PDF
- Splits by location when multiple locations are mentioned
- Creates separate hazard records for each location

✅ **Smart Location Extraction**
- Focuses on tourist/hazard-prone locations (Gilgit, Skardu, Naran, etc.)
- Filters out document header locations (Islamabad, Karachi, etc.) unless in context
- Maps locations to regions (e.g., "Murree" → "Murree & Galyat")

## How It Works

1. **Scraper finds advisory** → Gets title, date, URL
2. **Checks if PDF** → If `secure-viewer` or `.pdf` URL
3. **Extracts PDF URL** → Converts `secure-viewer?file=...` to direct PDF URL
4. **Downloads PDF** → Fetches PDF content
5. **Parses PDF text** → Extracts all text from all pages
6. **Detects multiple hazards** → Looks for multiple locations/dates
7. **Creates hazard records** → One per location if multiple found

## Example

**Input:** One PDF advisory about "Drought Alert for Gilgit-Baltistan and KPK"

**Output:** 
- Hazard 1: "Drought Alert - Gilgit-Baltistan" (with Gilgit-Baltistan content)
- Hazard 2: "Drought Alert - KPK" (with KPK content)

## Dependencies

Added to `requirements.txt`:
- `PyPDF2==3.0.1` - PDF parsing library
- `pdfplumber==0.11.0` - Better text extraction (preferred)

## Testing

The scraper automatically processes PDFs when:
- API starts (startup scrape)
- User presses refresh button
- Manual poller run

## Notes

- PDFs are downloaded and parsed in real-time
- Content is limited to 5000 characters per hazard
- Multiple hazards from same PDF get unique hashes
- Location detection is smart - avoids false positives from document headers

