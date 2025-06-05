import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


class PolishElectionScraper:
    def __init__(self, use_selenium=False):  # Default to requests method
        self.base_url = "https://www.wybory.gov.pl"
        self.use_selenium = use_selenium
        self.driver = None

        # Always initialize session for fallback
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pl-PL,pl;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def setup_selenium_driver(self):
        """Setup Chrome driver with appropriate options"""
        if self.driver is None:
            try:
                chrome_options = Options()
                chrome_options.add_argument('--headless')  # Run in background
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--window-size=1920,1080')
                chrome_options.add_argument(
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

                self.driver = webdriver.Chrome(options=chrome_options)
                return self.driver
            except Exception as e:
                print(f"Failed to setup Selenium driver: {e}")
                print("Make sure ChromeDriver is installed and in your PATH")
                return None
        return self.driver

    def scrape_district_results_selenium(self, url):
        """
        Scrape election results using Selenium (handles JavaScript-loaded content)
        """
        try:
            driver = self.setup_selenium_driver()
            if driver is None:
                return None

            driver.get(url)

            # Wait for the specific table to load
            wait = WebDriverWait(driver, 10)
            table = wait.until(EC.presence_of_element_located((By.ID, "DataTables_Table_5")))

            # Get the page source after JavaScript has loaded
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            return self.extract_table_data(soup, url)

        except Exception as e:
            print(f"Error with Selenium scraping {url}: {e}")
            return None

    def scrape_district_results_requests(self, url):
        """
        Scrape election results using requests (faster but might miss JS content)
        """
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            return self.extract_table_data(soup, url)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def extract_table_data(self, soup, url):
        """
        Extract data from the specific table structure you mentioned
        """
        results = []

        # Find the specific table by ID or class
        table = soup.find('table', {'id': 'DataTables_Table_5'})

        if not table:
            # Fallback: look for table with the specific classes
            table = soup.find('table',
                              class_='table table-bordered table-striped table-hover clickable right1 dataTable no-footer')

        if not table:
            print(f"Could not find target table in {url}")
            return {'commissions': [], 'url': url}

        # Extract tbody content
        tbody = table.find('tbody')
        if not tbody:
            print(f"Could not find tbody in table for {url}")
            return {'commissions': [], 'url': url}

        # Extract header information to understand column structure
        thead = table.find('thead')
        headers = []
        if thead:
            header_row = thead.find('tr')
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]

        print(f"Found headers: {headers}")

        # Process each row in tbody
        rows = tbody.find_all('tr')
        print(f"Found {len(rows)} data rows")

        for i, row in enumerate(rows):
            cells = row.find_all(['td', 'th'])

            if len(cells) >= 6:  # Ensure we have enough columns
                # Extract data based on your table structure
                commission_data = {
                    'numer_komisji': cells[0].get_text(strip=True),
                    'granice': cells[1].get_text(strip=True),
                    'siedziba': cells[2].get_text(strip=True),
                    'glosy_nawrocki': self.extract_number(cells[3].get_text(strip=True)),
                    'procent_nawrocki': self.extract_percentage(cells[4].get_text(strip=True)),
                    'glosy_trzaskowski': self.extract_number(cells[5].get_text(strip=True)) if len(cells) > 5 else '',
                    'procent_trzaskowski': self.extract_percentage(cells[6].get_text(strip=True)) if len(
                        cells) > 6 else ''
                }

                # Add any additional columns that might exist
                for j, cell in enumerate(cells[7:], start=7):
                    commission_data[f'column_{j}'] = cell.get_text(strip=True)

                results.append(commission_data)
                print(f"Row {i + 1}: {commission_data}")

        return {
            'commissions': results,
            'headers': headers,
            'url': url,
            'total_rows': len(results)
        }

    def extract_number(self, text):
        """Extract numeric value from text"""
        import re
        # Remove any non-digit characters except spaces (for thousands separator)
        numbers = re.findall(r'\d+', text.replace(' ', ''))
        return int(''.join(numbers)) if numbers else 0

    def extract_percentage(self, text):
        """Extract percentage value from text"""
        import re
        # Look for decimal numbers followed by %
        match = re.search(r'(\d+(?:,\d+)?)', text.replace(',', '.'))
        return float(match.group(1)) if match else 0.0

    def scrape_district_results(self, url):
        """
        Main method to scrape district results - tries Selenium first, then falls back to requests
        """
        if self.use_selenium:
            result = self.scrape_district_results_selenium(url)
            if result and result['commissions']:
                return result

        # Fallback to requests method
        print("Trying requests method as fallback...")
        return self.scrape_district_results_requests(url)

    def scrape_multiple_districts(self, district_codes):
        """
        Scrape results from multiple districts
        """
        all_results = []

        for code in district_codes:
            url = f"https://www.wybory.gov.pl/prezydent2025/pl/2/wynik/pow/{code}"
            print(f"\nScraping district {code}...")

            result = self.scrape_district_results(url)
            if result:
                result['district_code'] = code
                all_results.append(result)
                print(f"Successfully scraped {len(result['commissions'])} commissions from district {code}")
            else:
                print(f"Failed to scrape district {code}")

            # Be respectful - add delay between requests
            time.sleep(2)

        return all_results

    def save_to_csv(self, results, filename='election_results.csv'):
        """
        Save scraped results to CSV file
        """
        all_commissions = []

        for district_result in results:
            district_code = district_result.get('district_code', 'unknown')

            for commission in district_result.get('commissions', []):
                commission['district_code'] = district_code
                commission['district_url'] = district_result.get('url', '')
                all_commissions.append(commission)

        if all_commissions:
            df = pd.DataFrame(all_commissions)
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"Results saved to {filename} ({len(all_commissions)} total commissions)")
            return df
        else:
            print("No data to save!")
            return pd.DataFrame()

    def close(self):
        """Clean up resources"""
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()


# Example usage
if __name__ == "__main__":
    # You can choose to use Selenium (True) or just requests (False)
    scraper = PolishElectionScraper(use_selenium=False)

    try:
        # Test single district
        print("Testing single district scraping...")
        single_result = scraper.scrape_district_results("https://www.wybory.gov.pl/prezydent2025/pl/2/wynik/pow/226200")

        if single_result and single_result['commissions']:
            print(f"\nSuccessfully scraped {len(single_result['commissions'])} commissions!")
            print("Sample commission data:")
            for commission in single_result['commissions'][:3]:  # Show first 3 commissions
                print(commission)
        else:
            print("No data found or scraping failed")

        # Uncomment to scrape multiple districts
        # district_codes = ['226200', '226201', '226202']
        # all_results = scraper.scrape_multiple_districts(district_codes)
        # df = scraper.save_to_csv(all_results)

    finally:
        scraper.close()  # Clean up Selenium driver