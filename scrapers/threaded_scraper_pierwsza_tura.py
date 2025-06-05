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
failed = []
head = "nr_powiatu;Obwodowa Komisja Wyborcza nr;BARTOSZEWICZ Artur;BIEJAT Magdalena Agnieszka;BRAUN Grzegorz Michał;HOŁOWNIA Szymon Franciszek;JAKUBIAK Marek;MACIAK Maciej;MENTZEN Sławomir Jerzy;NAWROCKI Karol Tadeusz;SENYSZYN Joanna;STANOWSKI Krzysztof Jakub;TRZASKOWSKI Rafał Kazimierz;WOCH Marek Marian;ZANDBERG Adrian Tadeusz;"
lines.append(head)

def scrape_powiatu(url):
    options = get_chrome_options()
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    line = "XXXX;"

    try:
        driver.set_page_load_timeout(15)
        driver.get(url)

        komisja = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[4]/div[12]/h1'))
        )

        komisja = komisja.text.strip()

        komisja = komisja.split(" w pierwszym głosowaniu")[0]

        komisja+= ";"

        line += komisja

        table_element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[4]/div[12]/div[3]/div/table[4]/tbody'))
        )
        rows = table_element.find_elements(By.TAG_NAME, 'tr')
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, 'td') or row.find_elements(By.TAG_NAME, 'th')
            cell_values = [cell.text.strip() for cell in cells]
            formatted_line = cell_values[2] + ";"
            line += formatted_line
        with lock:
            lines.append(line)
    except Exception as e:
        failed.append(url)
        print(f"[{url}] Scraping failed: {e}")
    finally:
        driver.quit()
        print(f"[{url}] Done.")

if __name__ == "__main__":
    print("Started scraping...")

    # with open('teryt2.txt', 'r', encoding='utf-8') as f:
    #     teryts = [line.strip() for line in f if line.strip()]
    #
    # with open('teryt_powiaty.txt', 'r', encoding='utf-8') as f:
    #     teryts_powiaty = [line.strip() for line in f if line.strip()]
    #
    # teryts_described = [[teryt, 'g'] for teryt in teryts]
    # teryts_powiaty_described = [[teryt, 'p'] for teryt in teryts_powiaty]
    # teryts = teryts_described + teryts_powiaty_described

    with open('Tert_data/linki.txt', 'r') as file:
        linki = [line.strip() for line in file if line.strip()]

    # with ThreadPoolExecutor(max_workers=1) as executor:
    #     futures = [executor.submit(scrape_powiatu, nr) for nr in linki]
    #
    #     for future in as_completed(futures):
    #         future.result()

    scrape_powiatu(linki[0])

    with open('../results/wyniki_wyborow_pierwsza_tura.csv', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print("Scraping finished.")
    print (f"Failed to scrape {len(failed)} powiats:")
    for teryt in failed:
        print(teryt)
