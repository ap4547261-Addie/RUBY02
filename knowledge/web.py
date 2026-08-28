import urllib.request
import urllib.parse
import json
import re

def fetch_web_content(url: str) -> str:
    """Fetches text content from a given URL for Ruby's knowledge retrieval."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) RubyEngine/1.0"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            html_bytes = response.read()
            html_text = html_bytes.decode('utf-8', errors='ignore')
            
            # Basic HTML tag stripping to extract readable text
            clean_text = re.sub('<[^<]+?>', '', html_text)
            # Clean up extra whitespaces and newlines
            clean_text = ' '.join(clean_text.split())
            
            # Return a manageable snippet
            return clean_text[:4000]
    except Exception as e:
        return f"Error fetching web content: {str(e)}"
        
