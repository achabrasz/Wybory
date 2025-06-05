import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re

# Set up Chrome options
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')

# Set up driver path (adjust this to your actual path)
service = Service('../assets/chromedriver.exe')  # Replace with your path
driver = webdriver.Chrome(service=service, options=options)

nr_powiatu = '20101'  # Example value, adjust as needed
lines = []
header = "nr_powiatu;Obwodowa Komisja Wyborcza nr;Liczba głosów na NAWROCKI Karol Tadeusz;Procent głosów na NAWROCKI Karol Tadeusz;Liczba głosów na TRZASKOWSKI Rafał Kazimierz;Procent głosów na TRZASKOWSKI Rafał Kazimierz;"
lines.append(header)

def scrape_powiatu(nr_powiatu):
    # Open the URL
    if (nr_powiatu[-1] == '0'):
        url = 'https://www.wybory.gov.pl/prezydent2025/pl/2/wynik/pow/' + nr_powiatu
    else:
        url = 'https://www.wybory.gov.pl/prezydent2025/pl/2/wynik/gm/' + nr_powiatu

    try:
        driver.set_page_load_timeout(1)
        driver.get(url)
    except Exception as load_error:
        print(f"Page load failed: {load_error}")
        return

    try:
        try:
            table_element = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/div[4]/div[14]/div[8]/div/div[2]/div/table'))
            )
        except Exception as table_error:
            print(f"Table not found or took too long: {table_error}")
            return

        # Now extract all rows from the table
        rows = table_element.find_elements(By.TAG_NAME, 'tr')
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, 'td') or row.find_elements(By.TAG_NAME, 'th')
            cell_values = [cell.text.strip() for cell in cells]
            if not cell_values or all(v == '' for v in cell_values):
                continue  # skip empty rows

            # Find the cell that contains the full info (as in your example)
            long_text = next((v for v in cell_values if 'Obwodowa Komisja Wyborcza nr' in v), None)
            if long_text:
                # Extract fields with regex or string splits
                try:
                    okw_match = re.search(r'(Obwodowa Komisja Wyborcza nr \d+)', long_text)
                    nazwisko1_votes = re.search(r'Liczba głosów na NAWROCKI Karol Tadeusz:\s*(\d+)', long_text)
                    nazwisko1_pct = re.search(r'Procent głosów na NAWROCKI Karol Tadeusz:\s*([\d,]+%)', long_text)
                    nazwisko2_votes = re.search(r'Liczba głosów na TRZASKOWSKI Rafał Kazimierz:\s*([\d\s]+)', long_text)
                    nazwisko2_pct = re.search(r'Procent głosów na TRZASKOWSKI Rafał Kazimierz:\s*([\d,]+%)', long_text)

                    formatted_line = f"{nr_powiatu};{okw_match.group(1)};" \
                                     f"{nazwisko1_votes.group(1)};" \
                                     f"{nazwisko1_pct.group(1)};" \
                                     f"{nazwisko2_votes.group(1).strip()};" \
                                     f"{nazwisko2_pct.group(1)};"
                    lines.append(formatted_line)
                    print("Finished", nr_powiatu)

                except Exception as parse_error:
                    print(f"Could not parse row: {parse_error}\nText: {long_text}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Started scraping")
    with open('teryt.txt', 'r', encoding='utf-8') as f:
        teryts = [line.strip() for line in f]
    # You can loop through multiple powiats if needed
    for nr_teryt in teryts:
        scrape_powiatu(nr_teryt)
    # Save results to a file
    with open('../results/wyniki_wyborow_druga_tura.csv', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))