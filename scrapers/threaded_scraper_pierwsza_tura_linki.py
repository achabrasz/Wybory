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

def scrape_powiatu(teryt):
    options = get_chrome_options()
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    nr_powiatu = teryt[0]
    typ_powiatu = teryt[1]
    links = []

    try:
        if typ_powiatu == 'p':
            url = f'https://www.wybory.gov.pl/prezydent2025/pl/wynik/pow/{nr_powiatu}'
        else:
            url = f'https://www.wybory.gov.pl/prezydent2025/pl/wynik/gm/{nr_powiatu}'

        driver.set_page_load_timeout(15)
        driver.get(url)

        table_element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[4]/div[14]/div[8]/div/div[2]/div/table'))
        )
        rows = table_element.find_elements(By.TAG_NAME, 'tr')
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, 'td') or row.find_elements(By.TAG_NAME, 'th')
            for cell in cells:
                link = cell.find_elements(By.TAG_NAME, 'a')
                link_value = link[0].get_attribute('href') if link else None
                if link_value:
                    link_value = f"{nr_powiatu}" + ';' + link_value
                if link_value and link_value not in links:
                    links.append(link_value)
        for link in links:
            with lock:
                lines.append(link)
    except Exception as e:
        failed.append(teryt)
        print(f"[{nr_powiatu}] Scraping failed: {e}")
    finally:
        driver.quit()
        print(f"[{nr_powiatu}] Done.")

if __name__ == "__main__":
    print("Started scraping...")

    with open('teryt2.txt', 'r', encoding='utf-8') as f:
        teryts = [line.strip() for line in f if line.strip()]

    with open('teryt_powiaty.txt', 'r', encoding='utf-8') as f:
        teryts_powiaty = [line.strip() for line in f if line.strip()]

    teryts_described = [[teryt, 'g'] for teryt in teryts]
    teryts_powiaty_described = [[teryt, 'p'] for teryt in teryts_powiaty]
    teryts = teryts_described + teryts_powiaty_described

    # with open('failed.txt', 'r') as file:
    #     teryts = [line.strip() for line in file if line.strip()]

    # #strip teryt of "and []
    # teryts = [teryt.strip('[]') for teryt in teryts]
    # parsed_data = [item.strip("'").split(", ") for item in teryts]

    # # Remove the single quotes around each element
    # parsed_data = [[x.strip("'") for x in sublist] for sublist in parsed_data]
    # teryts = parsed_data

    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = [executor.submit(scrape_powiatu, nr) for nr in teryts]

        for future in as_completed(futures):
            future.result()

    with open('Tert_data/linki_2.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print("Scraping finished.")
    print (f"Failed to scrape {len(failed)} powiats:")
    for teryt in failed:
        print(teryt)

    failed_1 = len(failed)

    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = [executor.submit(scrape_powiatu, nr) for nr in teryts]

        for future in as_completed(futures):
            future.result()

    with open('Tert_data/linki_3.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print("Scraping 2 finished.")
    print(f"Failed to scrape {len(failed)} powiats:")
    for teryt in failed:
        print(teryt)

    print(f"first failed: {failed_1}")