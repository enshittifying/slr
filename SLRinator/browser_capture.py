#!/usr/bin/env python3
"""
Browser HTML Capture Tool
Captures the fully rendered HTML from a browser (including dynamically loaded content)
when a keyboard shortcut is pressed, and saves it to a file.
"""

import os
import re
import time
import threading
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import keyboard
from datetime import datetime

class BrowserCapture:
    def __init__(self):
        self.driver = None
        self.capture_count = 0
        self.running = True
        self.setup_browser()
        self.start_heartbeat()
        
    def setup_browser(self):
        """Initialize Chrome browser with Selenium"""
        chrome_options = Options()
        # Keep browser visible so you can interact with it
        # chrome_options.add_argument("--headless")  # Uncomment for headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✓ Browser initialized successfully")
        except Exception as e:
            print(f"Error initializing browser: {e}")
            print("\nMake sure you have Chrome and ChromeDriver installed:")
            print("  - Chrome: https://www.google.com/chrome/")
            print("  - ChromeDriver: pip install selenium")
            exit(1)
    
    def get_filename_from_url(self, url):
        """Extract filename from URL (last part after / and before .)"""
        parsed = urlparse(url)
        path = parsed.path.rstrip('/')
        
        if not path or path == '/':
            # Use domain name if no path
            filename = parsed.netloc.replace('.', '_')
        else:
            # Get the last segment of the path
            filename = path.split('/')[-1]
            
            # Remove file extension if present
            if '.' in filename:
                filename = filename.rsplit('.', 1)[0]
        
        # Clean up filename (remove special characters)
        filename = re.sub(r'[^\w\-_]', '_', filename)
        
        # Add timestamp to avoid overwriting
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return f"{filename}_{timestamp}.html"
    
    def capture_page(self):
        """Capture the current page's rendered HTML"""
        print("\n🔵 F5 pressed - Starting capture...")
        try:
            # Switch to the active window in case focus changed
            self.driver.switch_to.window(self.driver.current_window_handle)
            current_url = self.driver.current_url
            print(f"📸 Capturing: {current_url}")
            
            # Wait a moment for any dynamic content to load
            time.sleep(1)
            
            # Get the entire page source (rendered HTML)
            page_source = self.driver.page_source
            
            # Get filename based on URL
            filename = self.get_filename_from_url(current_url)
            
            # Create captures directory if it doesn't exist in current working directory
            captures_dir = os.path.join(os.getcwd(), "captures")
            os.makedirs(captures_dir, exist_ok=True)
            filepath = os.path.join(captures_dir, filename)
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(page_source)
            
            print(f"✓ Saved to: {filepath}")
            print(f"  Size: {len(page_source):,} bytes")
            
            self.capture_count += 1
            print(f"  📊 Total captures this session: {self.capture_count}")
            print("\n🟢 Ready for next capture (F5) or quit (ESC)")
            
        except Exception as e:
            print(f"❌ Error capturing page: {e}")
            print("Try pressing F5 again or check if browser window is still open")
    
    def navigate_to(self, url):
        """Navigate to a specific URL"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            self.driver.get(url)
            print(f"✓ Navigated to: {url}")
            # Wait for page to start loading
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except Exception as e:
            print(f"❌ Error navigating to {url}: {e}")
    
    def run(self):
        """Main loop - listen for keyboard shortcuts"""
        print("\n" + "="*60)
        print("BROWSER CAPTURE TOOL")
        print("="*60)
        print("\nInstructions:")
        print("  1. The browser window will open")
        print("  2. Navigate to any website")
        print("  3. Press 'F5' to capture the page")
        print("  4. Press 'ESC' to quit")
        print("\nShortcuts:")
        print("  • F5           : Capture current page")
        print("  • F6           : Go to URL (enter in terminal)")
        print("  • ESC          : Quit application")
        print("\n" + "="*60)
        
        # Navigate to initial page
        self.navigate_to("google.com")
        
        # Register keyboard shortcuts
        print("\n🔧 Registering keyboard shortcuts...")
        keyboard.add_hotkey('f5', self.capture_page)
        keyboard.add_hotkey('f6', self.prompt_for_url)
        print("✓ Shortcuts registered successfully")
        
        print("\n🟢 Ready! Use the browser and press shortcuts when needed.")
        print("   • F5 = Capture page")
        print("   • F6 = Enter new URL")  
        print("   • ESC = Quit\n")
        
        # Keep running until ESC is pressed
        try:
            keyboard.wait('esc')
        except Exception as e:
            print(f"\n⚠️  Keyboard listener stopped: {e}")
            print("Press CTRL+C in terminal to exit...")
            # Keep the browser open even if keyboard fails
            while True:
                time.sleep(1)
        
        print("\n👋 Closing browser and exiting...")
        self.cleanup()
    
    def prompt_for_url(self):
        """Prompt user for a new URL to navigate to"""
        print("\n" + "-"*40)
        new_url = input("Enter URL to navigate to: ").strip()
        if new_url:
            self.navigate_to(new_url)
    
    def start_heartbeat(self):
        """Start a background thread to keep the connection alive"""
        def heartbeat():
            while self.running:
                try:
                    # Just check if browser is still responsive
                    if self.driver:
                        _ = self.driver.title
                except:
                    pass
                time.sleep(5)
        
        thread = threading.Thread(target=heartbeat, daemon=True)
        thread.start()
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        if self.driver:
            self.driver.quit()

def main():
    # Check if captures directory exists in current working directory, create if not
    captures_dir = os.path.join(os.getcwd(), "captures")
    if not os.path.exists(captures_dir):
        os.makedirs(captures_dir)
        print(f"Created 'captures' directory at: {captures_dir}")
    
    try:
        app = BrowserCapture()
        app.run()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()