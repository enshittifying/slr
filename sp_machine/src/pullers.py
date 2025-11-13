"""
Functions for pulling different types of sources.
"""
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from weasyprint import HTML

def pull_website(url: str, output_dir: str, source_number: int, short_name: str):
    """Pull a website and save it as a PDF."""
    print(f"Pulling website: {url}")

    # Setup selenium
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Get page source
        driver.get(url)
        html_content = driver.page_source

        # Convert to PDF
        pdf_filename = f"SP-{source_number:03d}-{short_name}.pdf"
        pdf_path = os.path.join(output_dir, pdf_filename)
        HTML(string=html_content).write_pdf(pdf_path)

        print(f"✓ Saved to: {pdf_path}")
        return pdf_path

    except Exception as e:
        print(f"❌ Error pulling website: {e}")
        return None

    finally:
        driver.quit()
