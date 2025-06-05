import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import threading

# Set up Chrome options
def get_chrome_options():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    return options

# Path to your chromedriver
CHROMEDRIVER_PATH = '../assets/chromedriver.exe'

# Lock for writing lines thread-safely
lock = threading.Lock()
lines = []
header = "nr_powiatu;Obwodowa Komisja Wyborcza nr;Liczba głosów na NAWROCKI Karol Tadeusz;Procent głosów na NAWROCKI Karol Tadeusz;Liczba głosów na TRZASKOWSKI Rafał Kazimierz;Procent głosów na TRZASKOWSKI Rafał Kazimierz;"
lines.append(header)
failed = []

def scrape_powiatu(teryt):
    options = get_chrome_options()
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    nr_powiatu = teryt[0]
    typ_powiatu = teryt[1]

    try:
        if typ_powiatu == 'p':
            url = f'https://www.wybory.gov.pl/prezydent2025/pl/2/wynik/pow/{nr_powiatu}'
        else:
            url = f'https://www.wybory.gov.pl/prezydent2025/pl/2/wynik/gm/{nr_powiatu}'

        driver.set_page_load_timeout(15)
        driver.get(url)

        table_element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[4]/div[14]/div[8]/div/div[2]/div/table'))
        )
        rows = table_element.find_elements(By.TAG_NAME, 'tr')
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, 'td') or row.find_elements(By.TAG_NAME, 'th')
            cell_values = [cell.text.strip() for cell in cells]
            if not cell_values or all(v == '' for v in cell_values):
                continue

            long_text = next((v for v in cell_values if 'Obwodowa Komisja Wyborcza nr' in v), None)
            if long_text:
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

                    with lock:
                        lines.append(formatted_line)
                except Exception as parse_error:
                    failed.append(teryt)
                    print(f"[{nr_powiatu}] Parse error: {parse_error}")
    except Exception as e:
        failed.append(teryt)
        print(f"[{nr_powiatu}] Scraping failed: {e}")
    finally:
        driver.quit()
        print(f"[{nr_powiatu}] Done.")

if __name__ == "__main__":
    print("Started scraping...")

    # with open('teryt2.txt', 'r', encoding='utf-8') as f:
    #     teryts = [line.strip() for line in f if line.strip()]
    #
    # with open('teryt_powiaty.txt', 'r', encoding='utf-8') as f:
    #     teryts_powiaty = [line.strip() for line in f if line.strip()]
    #
    # #create a pair of teryt and g
    # teryts_described = [[teryt, 'g'] for teryt in teryts]
    # teryts_powiaty_described = [[teryt, 'p'] for teryt in teryts_powiaty]
    # teryts = teryts_described + teryts_powiaty_described

    #failed ones
    teryts = [['100505', 'g'], ['101402', 'g'], ['121806', 'g'], ['146100', 'p'], ['126200', 'p'], ['106200', 'p'], ['86100', 'p'], ['46400', 'p']]

    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(scrape_powiatu, nr) for nr in teryts]

        for future in as_completed(futures):
            future.result()

    with open('../results/wyniki_wyborow_druga_tura_2.csv', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print("Scraping finished.")
    print (f"Failed to scrape {len(failed)} powiats:")
    for teryt in failed:
        print(teryt)
