from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import os

class TestBookScraper:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        # Tell Selenium where Chromium is installed
        chrome_options.binary_location = "/usr/bin/chromium"

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

    def scrape_test_series(self, url, timer_minutes):
        self.driver.get(url)
        
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".test-series-card, .testCard"))
            )
            
            self._scroll_page()
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            test_cards = soup.select('.test-series-card:not(.free), .testCard:not(.free)')
            
            if not test_cards:
                return []
            
            results = []
            for i, card in enumerate(test_cards[:3]):  # Limit to 3 tests
                try:
                    test_id = card.get('data-test-id', f"mock_{i}")
                    test_title = self._get_test_title(card)
                    
                    filename = f"templates/mock_test_{test_id}.html"
                    self._generate_html(test_title, str(card), timer_minutes, filename)
                    
                    results.append({
                        'id': test_id,
                        'title': test_title,
                        'html_file': filename
                    })
                except Exception as e:
                    print(f"Error processing test card {i}: {e}")
                    continue
            
            return results
        finally:
            self.driver.quit()

    def _get_test_title(self, card):
        title_elem = card.select_one('.test-series-card__title, .testCard__title, [class*="title"]')
        return title_elem.get_text(strip=True) if title_elem else "Mock Test"

    def _scroll_page(self):
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def _generate_html(self, title, content, minutes, filename):
        with open('templates/mock_test.html', 'r') as f:
            template = f.read()
        
        html_content = template.replace('{{test_title}}', title)
        html_content = html_content.replace('{{test_content}}', content)
        html_content = html_content.replace('{{timer_minutes}}', str(minutes))
        
        os.makedirs('templates', exist_ok=True)
        with open(filename, 'w') as f:
            f.write(html_content)
