import os
import urllib.request
import urllib.parse
from html.parser import HTMLParser
from playwright.sync_api import sync_playwright

class HTMLTextExtractor(HTMLParser):
    """Simple parser to strip HTML tags and extract readable text from pages."""
    def __init__(self):
        super().__init__()
        self.text_result = []

    def handle_data(self, data):
        text = data.strip()
        if text:
            self.text_result.append(text)

    def get_text(self):
        return " ".join(self.text_result)

class BrowserTool:
    def __init__(self, user_data_dir=None):
        # Persistent profile path so Ruby inherits your logged-in social sessions
        self.user_data_dir = user_data_dir or os.path.expanduser("~/.ruby_browser_profile")

    def fetch_page_content(self, url: str, max_chars: int = 3000) -> str:
        """Lightweight HTTP fetcher for quick public web pages and articles."""
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                html_bytes = response.read()
                html_content = html_bytes.decode("utf-8", errors="ignore")
                
                parser = HTMLTextExtractor()
                parser.feed(html_content)
                return parser.get_text()[:max_chars]
        except Exception as e:
            return f"Error fetching page: {str(e)}"

    def web_search(self, query: str) -> str:
        """Performs a programmatic search query via DuckDuckGo."""
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        try:
            req = urllib.request.Request(
                search_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                html_content = response.read().decode("utf-8", errors="ignore")
                parser = HTMLTextExtractor()
                parser.feed(html_content)
                return parser.get_text()[:2000]
        except Exception as e:
            return f"Search failed: {str(e)}"

    def browse_social(self, url: str, action_type: str = "read", input_text: str = None) -> str:
        """
        Headless browser automation for social media platforms. 
        Runs in the background utilizing your saved session cookies.
        """
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=self.user_data_dir,
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                
                page = browser.new_page()
                page.goto(url, timeout=35000)
                page.wait_for_load_state("networkidle")
                
                # Perform specific action based on command intent
                if action_type == "post" and input_text:
                    # Generic input interaction placeholder for social post boxes
                    page.keyboard.type(input_text)
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(3000)
                    result = "Action completed: Successfully posted/interacted."
                else:
                    # Default read/extract visible text feed
                    result = page.evaluate("() => document.body.innerText")

                browser.close()
                return result[:3000]
            except Exception as e:
                return f"Social browser automation error: {s
                                                           tr(e)}"
