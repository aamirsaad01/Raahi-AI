"""
Debug script to inspect NDMA website structure
"""
import requests
from bs4 import BeautifulSoup
import json

def inspect_ndma_page():
    """Inspect the actual structure of NDMA advisories page"""
    url = "http://www.ndma.gov.pk/advisories"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        print("=" * 80)
        print("Fetching NDMA Advisories Page...")
        print("=" * 80)
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print(f"\n✅ Page loaded successfully")
        print(f"Title: {soup.title.string if soup.title else 'No title'}")
        print(f"\n{'=' * 80}")
        print("Looking for advisory links and content...")
        print("=" * 80)
        
        # Look for all links
        all_links = soup.find_all('a', href=True)
        print(f"\n📎 Found {len(all_links)} total links")
        
        advisory_links = []
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            if any(keyword in text.lower() or keyword in href.lower() 
                   for keyword in ['advisory', 'alert', 'warning', 'situation', 'sitrep']):
                advisory_links.append({
                    'text': text,
                    'href': href,
                    'full_url': href if href.startswith('http') else f"http://www.ndma.gov.pk{href}"
                })
        
        print(f"\n🔍 Found {len(advisory_links)} potential advisory links:")
        for i, link in enumerate(advisory_links[:20], 1):  # Show first 20
            print(f"{i}. {link['text'][:60]} -> {link['href']}")
        
        # Look for tables
        tables = soup.find_all('table')
        print(f"\n📊 Found {len(tables)} tables")
        if tables:
            for i, table in enumerate(tables[:3], 1):  # Show first 3 tables
                print(f"\nTable {i}:")
                rows = table.find_all('tr')
                print(f"  Rows: {len(rows)}")
                if rows:
                    # Show first few rows
                    for j, row in enumerate(rows[:5], 1):
                        cells = row.find_all(['td', 'th'])
                        cell_texts = [cell.get_text(strip=True) for cell in cells]
                        print(f"  Row {j}: {cell_texts}")
        
        # Look for lists
        lists = soup.find_all(['ul', 'ol'])
        print(f"\n📋 Found {len(lists)} lists")
        advisory_lists = []
        for lst in lists:
            items = lst.find_all('li')
            for item in items:
                text = item.get_text(strip=True)
                link = item.find('a', href=True)
                if any(keyword in text.lower() for keyword in ['advisory', 'alert', 'warning']):
                    advisory_lists.append({
                        'text': text,
                        'link': link['href'] if link else None
                    })
        
        if advisory_lists:
            print(f"\n🔍 Found {len(advisory_lists)} list items with advisory keywords:")
            for i, item in enumerate(advisory_lists[:10], 1):
                print(f"{i}. {item['text'][:80]}")
        
        # Look for divs with specific classes
        print(f"\n🔍 Looking for divs with advisory-related classes...")
        advisory_divs = soup.find_all('div', class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['advisory', 'alert', 'post', 'news', 'item']
        ))
        print(f"Found {len(advisory_divs)} divs with advisory-related classes")
        
        # Look for article tags
        articles = soup.find_all('article')
        print(f"\n📰 Found {len(articles)} article tags")
        
        # Save HTML for inspection
        with open('ndma_page_debug.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print(f"\n💾 Saved full HTML to: ndma_page_debug.html")
        
        # Look for specific patterns
        print(f"\n{'=' * 80}")
        print("Looking for date patterns...")
        print("=" * 80)
        date_patterns = soup.find_all(string=re.compile(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}'))
        print(f"Found {len(date_patterns)} potential date strings")
        for date_str in date_patterns[:10]:
            print(f"  - {date_str.strip()}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import re
    inspect_ndma_page()


