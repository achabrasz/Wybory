import pandas as pd

def scrape_teryt():
    # Read the CSV file containing TERYT codes
    teryt_df = pd.read_csv('Tert_data/wyniki_gl_na_kandydatow_po_gminach_w_drugiej_turze_utf8.csv', sep=';')

    # Extract the TERYT codes from the DataFrame
    teryt_codes = teryt_df['TERYT Gminy'].tolist()

    #remove .0 from the codes
    teryt_codes = [str(int(code)) for code in teryt_codes if pd.notna(code)]


    # Create a list to store the results
    return teryt_codes

def scrape_teryt_from_cities():
    # Read the CSV file containing TERYT codes for cities
    teryt_df = pd.read_csv('Tert_data/wyniki_gl_na_kandydatow_po_powiatach_w_drugiej_turze_utf8.csv', sep=';')

    # Extract the TERYT codes from the DataFrame where column Powiat start with an uppercase letter
    teryt_codes = teryt_df['TERYT Powiatu'].tolist()
    powiaty = teryt_df['Powiat'].tolist()
    teryt_codes_cleaned = []
    for code, powiat in zip(teryt_codes, powiaty):
        if pd.notna(code) and powiat[0].isupper():
            teryt_codes_cleaned.append(str(int(code)))

    #remove .0 from the codes
    teryt_codes_cleaned = [str(int(code)) for code in teryt_codes_cleaned if pd.notna(code)]

    return teryt_codes_cleaned

if __name__ == "__main__":
    teryts = scrape_teryt()
    teryts_powiaty = scrape_teryt_from_cities()
    with open('teryt2.txt', 'w', encoding='utf-8') as f:
        for teryt in teryts:
            f.write(str(teryt) + '\n')
    with open('teryt_powiaty.txt', 'w', encoding='utf-8') as f:
        for teryt in teryts_powiaty:
            f.write(str(teryt) + '\n')