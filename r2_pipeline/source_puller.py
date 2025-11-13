#!/usr/bin/env python3
"""
Source Puller
"""

import os
import re
import time
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime

class SourcePuller:
    def __init__(self):
        self.driver = None
        self.setup_browser()

    def setup_browser(self):
        """Initialize Chrome browser with Selenium"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✓ Browser initialized successfully")
        except Exception as e:
            print(f"Error initializing browser: {e}")
            print("\nMake sure you have Chrome and ChromeDriver installed")
            exit(1)

    def get_filename_from_url(self, url, source_number, short_name):
        """Extract filename from URL"""
        
        filename = f"SP-{source_number:03d}-{short_name}.html"
        return filename

    def pull_source(self, url, source_number, short_name):
        """Capture the current page's rendered HTML"""
        print(f"\n🔵 Pulling source: {url}")
        try:
            # Make sure we have the current window
            if not self.driver.window_handles:
                print("❌ No browser window found")
                return
                
            self.driver.switch_to.window(self.driver.window_handles[0])
            
            self.navigate_to(url)
            
            # Wait for any dynamic content
            time.sleep(1)
            
            # Get the page source
            page_source = self.driver.page_source
            
            # Get filename and save
            filename = self.get_filename_from_url(url, source_number, short_name)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            captures_dir = os.path.join(script_dir, "pulled_sources")
            os.makedirs(captures_dir, exist_ok=True)
            filepath = os.path.join(captures_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(page_source)
            
            print(f"✓ Saved to: {filepath}")
            print(f"  Size: {len(page_source):,} bytes")
            
        except Exception as e:
            print(f"❌ Error: {e}")

    def navigate_to(self, url):
        """Navigate to a URL"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            self.driver.get(url)
            print(f"✓ Navigated to: {url}")
        except Exception as e:
            print(f"❌ Error navigating: {e}")

    def run(self):
        """Main loop"""
        print("\n" + "="*60)
        print("SOURCE PULLER")
        print("="*60)
        
        # For now, we'll use a dummy source list.
        # In the future, this will come from the Sourcepull spreadsheet.
        source_list = [
            {"number": 1, "short_name": "example", "url": "http://example.com"},
            {"number": 2, "short_name": "google", "url": "http://google.com"},
        ]
        
        for source in source_list:
            self.pull_source(source["url"], source["number"], source["short_name"])
            
        self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
        print("👋 Browser closed")

def main():
    try:
        app = SourcePuller()
        app.run()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
