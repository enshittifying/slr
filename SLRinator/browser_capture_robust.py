#!/usr/bin/env python3
"""
Browser HTML Capture Tool - Robust Version
Uses pynput instead of keyboard library for better stability
"""

import os
import re
import time
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime
from pynput import keyboard
from pynput.keyboard import Key, KeyCode
import threading

class BrowserCapture:
    def __init__(self):
        self.driver = None
        self.capture_count = 0
        self.running = True
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
    
    def get_filename_from_url(self, url):
        """Extract filename from URL"""
        parsed = urlparse(url)
        path = parsed.path.rstrip('/')
        
        if not path or path == '/':
            filename = parsed.netloc.replace('.', '_')
        else:
            filename = path.split('/')[-1]
            if '.' in filename:
                filename = filename.rsplit('.', 1)[0]
        
        filename = re.sub(r'[^\w\-_]', '_', filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return f"{filename}_{timestamp}.html"
    
    def capture_page(self):
        """Capture the current page's rendered HTML"""
        print("\n🔵 Capture triggered!")
        try:
            # Make sure we have the current window
            if not self.driver.window_handles:
                print("❌ No browser window found")
                return
                
            self.driver.switch_to.window(self.driver.window_handles[0])
            current_url = self.driver.current_url
            print(f"📸 Capturing: {current_url}")
            
            # Wait for any dynamic content
            time.sleep(1)
            
            # Get the page source
            page_source = self.driver.page_source
            
            # Get filename and save
            filename = self.get_filename_from_url(current_url)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            captures_dir = os.path.join(script_dir, "captures")
            os.makedirs(captures_dir, exist_ok=True)
            filepath = os.path.join(captures_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(page_source)
            
            print(f"✓ Saved to: {filepath}")
            print(f"  Size: {len(page_source):,} bytes")
            
            self.capture_count += 1
            print(f"  📊 Total captures: {self.capture_count}")
            print("\n🟢 Ready for next capture (CMD+SHIFT+0)")
            
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
        """Main loop with keyboard listener"""
        print("\n" + "="*60)
        print("BROWSER CAPTURE TOOL")
        print("="*60)
        print("\nInstructions:")
        print("  1. Browser window is open")
        print("  2. Navigate to any website")
        print("  3. Press CMD+SHIFT+0 to capture")
        print("  4. Press ESC to quit")
        print("\n" + "="*60)
        
        # Navigate to initial page
        self.navigate_to("google.com")
        
        # Track pressed keys
        current_keys = set()
        
        def on_press(key):
            current_keys.add(key)
            
            # Check for CMD+SHIFT+0 (on Mac)
            if (Key.cmd in current_keys and 
                Key.shift in current_keys and 
                KeyCode.from_char('0') in current_keys):
                # Run capture in separate thread to not block keyboard listener
                threading.Thread(target=self.capture_page).start()
                return
            
            # Check for ESC to quit
            if key == Key.esc:
                print("\n👋 Exiting...")
                self.running = False
                return False
        
        def on_release(key):
            try:
                current_keys.remove(key)
            except KeyError:
                pass
        
        print("\n🟢 Ready! Press CMD+SHIFT+0 to capture, ESC to quit\n")
        
        # Start keyboard listener
        with keyboard.Listener(
            on_press=on_press,
            on_release=on_release) as listener:
            listener.join()
        
        self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        if self.driver:
            self.driver.quit()
        print("👋 Browser closed")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    captures_dir = os.path.join(script_dir, "captures")
    if not os.path.exists(captures_dir):
        os.makedirs(captures_dir)
        print(f"Created captures directory at: {captures_dir}")
    
    try:
        app = BrowserCapture()
        app.run()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()