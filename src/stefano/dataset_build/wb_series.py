import os
import pandas as pd
import wbgapi as wb


DATA = "../data"
INDICATORS = "../indicators"


def filter_valid_economies(codes:list, countries:list, warning=True):
    valid = []
    for i in range(len(codes)):
        try:
            wb.economy.get(codes[i])
            if warning:
                print("-", codes[i], countries[i])
            valid.append(codes[i])
        except:
            if warning:
                print("-", f"{codes[i]}, {countries[i]} ⚠ ️This country does not exist!")
    return valid


def list_olympic_countries(warning:bool=False):
    df = pd.read_csv(os.path.join(DATA, "Olympic_Country_Profiles.csv"))
    codes = df["noc"].unique().tolist()
    countries = df["country"].unique().tolist()
    return filter_valid_economies(codes, countries, warning=warning)


def years_to_int(years:list):
    int_years = []
    for year in years:
        year = year[2:]
        int_years.append(int(year))
    return int_years


def download_series(country:str, series:list, time_range:range, output_csv=None):

    if output_csv is None:
        output_csv = country + ".csv"

    dataframes = []
    for item in series:
        db_id     = item[0]
        series_id = item[1]
        df = wb.data.DataFrame(db=db_id, series=series_id, time=time_range, economy=country).T
        df.index.name = "Year"
        df.rename(columns={country: series_id}, inplace=True)
        dataframes.append(df)

    df = pd.concat(dataframes, axis=1, ignore_index=False)
    df.to_csv(output_csv, index=True)


def main():

    series = [
        (16, "SE.ADT.LITR.FE.ZS", "Literacy rate, adult female (% of females ages 15 and above)"),
        (16, "SE.ADT.LITR.MA.ZS", "Literacy rate, adult male (% of males ages 15 and above)"),
        (16, "SE.ADT.LITR.ZS",    "Literacy rate, adult total (% of people ages 15 and above)"),
        (16, "SE.TER.ENRR",       "School enrollment, tertiary (% gross)"),
        (16, "SE.TER.ENRR.FE",    "School enrollment, tertiary, female (% gross)"),
        (16, "SE.XPD.TOTL.GD.ZS", "Public spending on education, total (% of GDP)"),
        (16, "SP.DYN.SMAM.FE",    "Age at first marriage, female"),
        (16, "SP.DYN.SMAM.MA",    "Age at first marriage, male"),
        (12, "HD.HCI.LAYS",       "Human Capital Index (HCI): Learning-Adjusted Years of School, Total"),
        (12, "HD.HCI.LAYS.FE",    "Human Capital Index (HCI): Learning-Adjusted Years of School, Female"),
        (12, "HD.HCI.LAYS.MA",    "Human Capital Index (HCI): Learning-Adjusted Years of School, Male")
    ]

    years = range(1960, 2020)

    for country in list_olympic_countries(warning=True):
        print(country + "...")
        file_path = os.path.join(INDICATORS, country + ".csv")
        download_series(country, series, years, output_csv=file_path)
        print("Done\n")

if __name__ == "__main__":
    main()

