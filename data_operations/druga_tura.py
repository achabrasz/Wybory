import pandas as pd
import numpy as np

class ElectionClass:
    def __init__(self):
        self.nawrocki_official_1 = 5790804
        self.trzaskowski_official_1 = 6147797
        self.glosy_official_1 = 19603784
        self.glosy_correction_1 = 0
        self.nawrocki_official_2 = 10606877
        self.trzaskowski_official_2 = 10237286
        self.glosy_official_2 = 20844163
        self.glosy_correction_2 = 0
        self.nawrocki_scrapped_sum_1 = 0
        self.trzaskowski_scrapped_sum_1 = 0
        self.glosy_scrapped_sum_1 = 0
        self.nawrocki_scrapped_correction_1 = 0
        self.trzaskowski_scrapped_correction_1 = 0
        self.nawrocki_scrapped_sum_2 = 0
        self.trzaskowski_scrapped_sum_2 = 0
        self.glosy_scrapped_sum_2 = 0
        self.nawrocki_scrapped_correction_2 = 0
        self.trzaskowski_scrapped_correction_2 = 0
        self.pt = pd.read_csv("../results/wyniki_wyborow_pierwsza_tura.csv", sep=";")
        self.dt = pd.read_csv("../results/2_tura_merged.csv", sep=";")
        self.matching_rows_1 = None
        self.matching_rows_2 = None
        self.difference_package = None

def initialize_data(election):
    election.pt = election.pt.iloc[:, :-1]
    election.dt = election.dt.iloc[:, :-1]
    election.pt.iloc[:, 1] = election.pt.iloc[:, 1].str.replace("numer", "nr")
    election.pt['nr_powiatu'] = election.pt['nr_powiatu'].astype(str)
    election.dt['nr_powiatu'] = election.dt['nr_powiatu'].astype(str)
    election.pt['nr_powiatu'] = election.pt['nr_powiatu'].str.strip()
    election.dt['nr_powiatu'] = election.dt['nr_powiatu'].str.strip()
    election.pt.iloc[:, 1] = election.pt.iloc[:, 1].astype(str)
    election.dt.iloc[:, 1] = election.dt.iloc[:, 1].astype(str)
    election.pt.iloc[:, 1] = election.pt.iloc[:, 1].str.strip()
    election.dt.iloc[:, 1] = election.dt.iloc[:, 1].str.strip()
    election.pt['Merged'] = election.pt['nr_powiatu'] + " " + election.pt.iloc[:, 1]
    election.dt['Merged'] = election.dt['nr_powiatu'] + " " + election.dt.iloc[:, 1]
    #remove duplicate rows in pt and dt
    election.pt = election.pt.drop_duplicates(subset=['Merged'])
    election.dt = election.dt.drop_duplicates(subset=['Merged'])
    #sort pt and dt by 'Merged'
    election.pt = election.pt.sort_values(by='Merged').reset_index(drop=True)
    election.dt = election.dt.sort_values(by='Merged').reset_index(drop=True)
    election.difference_package = election.dt['Merged'].isin(election.pt['Merged'])
    election.nawrocki_scrapped_sum_1 = pd.to_numeric(election.pt.iloc[:, 2], errors="coerce").sum()
    election.trzaskowski_scrapped_sum_1 = pd.to_numeric(election.pt.iloc[:, 4], errors="coerce").sum()
    election.nawrocki_scrapped_correction_1 = election.nawrocki_official_1 - election.nawrocki_scrapped_sum_1
    election.trzaskowski_scrapped_correction_1 = election.trzaskowski_official_1 - election.trzaskowski_scrapped_sum_1
    # election.glosy_scrapped_sum_1 = election.nawrocki_scrapped_sum_1 + election.trzaskowski_scrapped_sum_1
    # election.glosy_correction_1 = election.glosy_official_1 - (election.nawrocki_scrapped_sum_1 + election.trzaskowski_scrapped_sum_1)
    election.nawrocki_scrapped_sum_2 = pd.to_numeric(election.dt.iloc[:, 2], errors="coerce").sum()
    election.trzaskowski_scrapped_sum_2 = pd.to_numeric(election.dt.iloc[:, 4], errors="coerce").sum()
    election.glosy_scrapped_sum_2 = election.nawrocki_scrapped_sum_2 + election.trzaskowski_scrapped_sum_2
    election.nawrocki_scrapped_correction_2 = election.nawrocki_official_2 - election.nawrocki_scrapped_sum_2
    election.trzaskowski_scrapped_correction_2 = election.trzaskowski_official_2 - election.trzaskowski_scrapped_sum_2
    election.glosy_correction_2 = election.glosy_official_2 - election.glosy_scrapped_sum_2
    #switch values of 1 col from numer to nr in pt and dt


    #Match values of pt and dt
    election.matching_rows_1, election.matching_rows_2 = election.pt[(election.pt['nr_powiatu'].isin(election.dt['nr_powiatu']) &
                                                    election.pt.iloc[:, 1].isin(election.dt.iloc[:, 1]))], \
        election.dt[(election.dt['nr_powiatu'].isin(election.pt['nr_powiatu']) &
                     election.dt.iloc[:, 1].isin(election.pt.iloc[:, 1]))]

def find_rows_where_trzaskowski_less_in_first(election):
    temp_matching_rows_1 = election.matching_rows_1.copy()
    temp_matching_rows_2 = election.matching_rows_2.copy()
    #Leave only [Merged, TRZASKOWSKI Rafał Kazimierz, Liczba głosów na TRZASKOWSKI Rafał Kazimierz]
    temp_matching_rows_1 = temp_matching_rows_1[['Merged', 'TRZASKOWSKI Rafał Kazimierz']]
    temp_matching_rows_2 = temp_matching_rows_2[['Merged', 'Liczba głosów na TRZASKOWSKI Rafał Kazimierz']]
    #rename columns
    temp_matching_rows_1.columns = ['Merged', 'Trzaskowski']
    temp_matching_rows_2.columns = ['Merged', 'Trzaskowski']

    temp_matching_rows_1['Trzaskowski'] = pd.to_numeric(temp_matching_rows_1['Trzaskowski'], errors='coerce')
    temp_matching_rows_2['Trzaskowski'] = pd.to_numeric(temp_matching_rows_2['Trzaskowski'], errors='coerce')

    temp_list_1 = temp_matching_rows_1[['Merged', 'Trzaskowski']].values.tolist()
    temp_list_2 = temp_matching_rows_2[['Merged', 'Trzaskowski']].values.tolist()

    faulty_rows = []

    for row1, row2 in zip(temp_list_1, temp_list_2):
        if row1[1] > row2[1]:
            row2.append(row1[1])
            row2.append(row1[1] - row2[1])
            row2.append(row1[0])
            faulty_rows.append(row2)
    faulty_rows_df = pd.DataFrame(faulty_rows, columns=['Merged', 'Merged 2', 'Trzaskowski 2', 'Trzaskowski 1','Difference'])

    return faulty_rows_df



if __name__ == "__main__":
    election = ElectionClass()

    initialize_data(election)

    print(election.nawrocki_scrapped_correction_2)

    print(election.trzaskowski_scrapped_correction_2)

    print(election.difference_package)


    # election.pt['Match'] = (election.pt['nr_powiatu'].isin(election.dt['nr_powiatu'])
    #                         & election.pt.iloc[:, 1].isin(election.dt.iloc[:, 1]))
    # print(election.pt['Match'].value_counts())

    # Match rows

    print(election.matching_rows_1['Merged'])
    print(election.matching_rows_2['Merged'])

    # faulty = find_rows_where_trzaskowski_less_in_first(election)
    # with open("../results/druga_less", "w") as faulty_rows:
    #     faulty.to_csv(faulty_rows, sep=";", index=False)
    # print(faulty)


