#!/usr/bin/env python3
"""
Debug script to test scraping the LangChain documentation
Run this to see what content we can extract
"""

import requests
from bs4 import BeautifulSoup
import sys

def test_scraping(url):
    """Test scraping a URL and show what we find"""
    
    print(f"🔍 Testing URL: {url}\n")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        print("📡 Fetching page...")
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        print(f"✅ Response: {response.status_code}\n")
        
        print(f"📊 Content length: {len(response.content)} bytes\n")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check for title
        if soup.title:
            print(f"📄 Title: {soup.title.string}\n")
        
        # Try different selectors
        selectors = [
            ('article', soup.find('article')),
            ('main', soup.find('main')),
            ("div class='content'", soup.find('div', class_='content')),
            ("div role='main'", soup.find('div', {'role': 'main'})),
            ("div class='markdown'", soup.find('div', class_='markdown')),
            ("div id='content'", soup.find('div', id='content')),
            ("div class='docs-content'", soup.find('div', class_='docs-content')),
            ("div class='page-content'", soup.find('div', class_='page-content')),
        ]
        
        print("🔎 Testing selectors:\n")
        found_content = None
        
        for name, element in selectors:
            if element:
                text = element.get_text(strip=True)
                print(f"✅ {name:30} Found! Length: {len(text)} chars")
                if not found_content and len(text) > 300:
                    found_content = (name, element, text)
            else:
                print(f"❌ {name:30} Not found")
        
        print("\n" + "="*60 + "\n")
        
        if found_content:
            selector_name, element, text = found_content
            print(f"🎯 Best selector: {selector_name}")
            print(f"📏 Content length: {len(text)} chars\n")
            print("📝 First 500 characters:\n")
            print(text[:500])
            print("\n...")
            print(f"\n📝 Last 200 characters:\n")
            print("...")
            print(text[-200:])
        else:
            print("❌ No suitable content found!")
            print("\n🔍 Let's check what divs exist:\n")
            
            all_divs = soup.find_all('div')
            print(f"Found {len(all_divs)} div elements")
            
            # Find divs with classes
            divs_with_classes = [(d.get('class', []), len(d.get_text(strip=True))) 
                                 for d in all_divs if d.get('class')]
            divs_with_classes.sort(key=lambda x: x[1], reverse=True)
            
            print("\nTop 10 divs by content length:\n")
            for classes, length in divs_with_classes[:10]:
                print(f"  class={classes} -> {length} chars")
            
            # Try fallback: largest div
            if all_divs:
                largest = max(all_divs, key=lambda d: len(d.get_text(strip=True)))
                text = largest.get_text(strip=True)
                print(f"\n🔧 Fallback: Largest div has {len(text)} chars")
                if len(text) > 500:
                    print("Preview:")
                    print(text[:300])
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://docs.langchain.com/oss/python/langgraph/overview"
    test_scraping(url)