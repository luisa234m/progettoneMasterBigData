import os
import random
import time
import pandas as pd
import requests
import urllib3
import wbgapi as wb
import ac.utils

DATA = "./data"
INDICATORS = "./indicators/wb"

def filter_valid_economies(codes:list, countries:list, warning=True):
    """
    Prende i paesi passati alla funzione (i codici) e controlla che le sigle corrispondano
    alla nomenclatura World Bank. Nomi vengono salvati in un file per velocizzare
    chiamate multiple della funzione
    """
    valid = []
    file_path = "./data/valid.txt"
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            for i in range(len(codes)):
                try:
                    wb.economy.get(codes[i])

                    # Se richiesto viene mostrato un output a video
                    if warning:
                        print("-", codes[i], countries[i])
                    valid.append((codes[i], countries[i]))

                    # Salviamo in un file i codici validi
                    f.write(codes[i] + " " + countries[i] + "\n")

                    # Introduciamo un ritardo casuale per evitare che lo script venga bloccato
                    milliseconds = random.randint(1, 300)
                    time.sleep(milliseconds / 1000.0)

                except:
                    # Se richiesto, viene mostrato il fatto che il codice del paese non esiste in WB
                    if warning:
                        print("-", f"{codes[i]}, {countries[i]} ⚠ ️This country does not exist!")
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                code = line.split()[0]
                country = line.split()[1]
                valid.append((code, country))

    return valid

def list_olympic_countries(warning:bool=False):
    """
    Prende i codici dei paesi partecipanti alle Olimpiadi
    """
    encoding = ac.utils.detect_encoding("./data/ISO.csv")
    df = pd.read_csv("./data/ISO.csv", encoding=encoding)
    df.sort_values(by=["alpha-3"], inplace=True)
    codes = df["alpha-3"].tolist()
    countries = df["name"].tolist()
    return filter_valid_economies(codes, countries, warning=warning)

def years_to_int(years:list):
    """
    Conversione di una lista di anni dal formato stringa al numero intero
    """
    int_years = []
    for year in years:
        year = year[2:]
        int_years.append(int(year))
    return int_years

def download_series(country:str, series:list, time_range:range, output_csv=None):
    """
    Funzione per scaricare una serie di indicatori per paese. Salva in un dataframe
    al percorso passato in output_csv
    """
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

    # Inserimento manuale delle liste di indicatori dei vari partecipanti
    alessio = [
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

    db_id = 2
    santina = [
        (db_id, "AG.LND.PRCP.MM", "Average precipitation in depth (mm per year)"),
        (db_id, "EG.ELC.ACCS.ZS",  "Access to electricity (% of population)"),
        (db_id, "NY.GDP.MKTP.CD", "GDP (current US$)"),
        (db_id, "IT.NET.USER.ZS", "Individuals using the Internet (% of population)"),
        (db_id, "MS.MIL.XPND.CN", "Military expenditure (current LCU)"),
        (db_id, "NE.CON.GOVT.CD", "General government final consumption expenditure (current US$)"),
        (db_id, "NE.DAB.TOTL.CN", "Gross national expenditure (current LCU)"),
        (db_id, "NV.SRV.TOTL.CN", "Services, value added (current LCU)"),
        (db_id, "NY.GDP.DEFL.KD.ZG", "Inflation, GDP deflator (annual %)"),
        (db_id, "NY.GDP.MKTP.CN", "GDP (current LCU)"),
        (db_id, "NY.GNP.MKTP.CN", "GNI (current LCU)"),
        (db_id, "SE.PRM.ENRR", "School enrollment, primary (% gross)"),
        (db_id, "SE.SEC.ENRR", "School enrollment, secondary (% gross)"),
        (db_id, "SP.POP.TOTL", "Population, total"),
        (db_id, "SL.UEM.TOTL.ZS", "Unemployment, total (% of total labor force) (modeled ILO estimate)"),
        (db_id, "AG.SRF.TOTL.K2", "Surface area (sq. km)")
    ]

    db_id = 16
    alessia = [
        (db_id, "SH.XPD.CHEX.GD.ZS", "Current health expenditure (% of GDP)"),
        (db_id, "SH.STA.OWAD.ZS", "Prevalence of overweight (% of adults)"),
        (db_id, "SH.STA.BASS.ZS", "People using at least basic sanitation services (% of population)"),
        (db_id, "SP.DYN.LE00.IN", "life expectancy at birth, total(years)"),
        (db_id, "SH.DTH.NCOM.ZS", "Current health expenditure per capita, PPP (current international $)"),
        (db_id, "SH.H2O.SMDW.ZS", "People using at least basic drinking water services (% of population)"),
        (db_id, "SN.ITK.DEFC.ZS", "Prevalence of undernourishment (% of population)"),
        (db_id, "SH.HTN.PREV.ZS", "Prevalence of hypertension (% of adults ages 30-79)")
    ]

    luisa = [
        (db_id, "SN.ITK.DEFC.ZS", "Prevalence of undernourishment( % of population)"),
        (db_id, "SH.XPD.CHEX.GD.ZS", "Current health expenditure( % of GDP)"),
        (db_id, "SH.XPD.CHEX.PP.CD", "Current health expenditure per capita, PPP (current international $)"),
        (db_id, "SH.STA.DIAB.ZS", "Diabetes prevalence ( % of population ages 20 to 79)"),
        (db_id, "SH.DTH.NCOM.ZS", "Cause of death, by non-communicable diseases (% of total)"),
        (db_id, "SH.STA.AIRP.P5", "Air_Pollution_Mortality")
    ]

    stefano = []
    """stefano = [
        #(13, "IC.FRM.EMP.GROW.PEFT2", "Annual employment growth (%)"),
        (13, "IC.FRM.GEN.GEND4", "Percent of firms with a female top manager"),
        (13, "IC.FRM.GEN.GEND5", "Proportion of permanent full-time production workers that are female (%)"),
        (16, "SH.DTH.IMRT", "Number of infant deaths"),
        (16, "SH.STA.SUIC.P5", "Suicide mortality rate (per 100,000 population)"),
        (16, "SH.XPD.CHEX.GD.ZS", "Current health expenditure (% of GDP)"),
        (16, "SH.XPD.CHEX.PC.CD", "Current health expenditure per capita (current US$)"),
        (16, "SH.XPD.CHEX.PP.CD	", "Current health expenditure per capita, PPP (current international $)"),
        (16, "SH.XPD.GHED.CH.ZS", "Domestic general government health expenditure (% of current health expenditure)"),
        (16, "SH.XPD.GHED.GD.ZS", "Domestic general government health expenditure (% of GDP)"),
        #(16, "H.XPD.GHED.GE.ZS", "Domestic general government health expenditure (% of general government expenditure)"),
        (16, "SH.XPD.GHED.PC.CD", "Domestic general government health expenditure per capita (current US$)"),
        (16, "SH.XPD.GHED.PP.CD", "Domestic general government health expenditure per capita, PPP (current international $)"),
        (16, "SP.POP.TOTL", "Population, total"),
        (16, "SP.POP.TOTL.FE.ZS", "Population, female (% of total population)"),
        (16, "SP.POP.TOTL.MA.ZS", "Population, male (% of total population)"),
        (16, "SP.RUR.TOTL", "Rural population"),
        (16, "SP.RUR.TOTL.ZS", "Rural population (% of total population)"),
        (16, "SP.URB.TOTL.IN.ZS", "Urban population (% of total population)"),
        (18, "NY.GDP.PCAP.KD.ZG", "GDP per capita growth (annual %)"),
        (19, "EN.POP.SLUM.UR.ZS", "Population living in slums (% of urban population)"),
        (19, "IT.NET.USER.P2", "Internet users (per 100 people)"),
        (25, "IT.NET.USER.ZS", "Individuals using the Internet (% of population)"),
        (65, "HF.DYN.IMRT.IN", "Mortality rate, infant (per 1,000 live births)")
    ]"""

    db_id = 2
    gianni = [
        (db_id, "SP.POP.TOTL", "Popolazione Totale"),
        (db_id, "SP.POP.1564.TO.ZS", "Popolazione in età lavorativa (15-64 anni %)"),
        (db_id, "SP.URB.TOTL.IN.ZS", "Popolazione Urbana (%)"),
        (db_id, "NY.GDP.MKTP.CD", "PIL (Corrente USD)"),
        (db_id, "NY.GDP.PCAP.CD", "PIL pro capite (Corrente USD)"),
        (db_id, "SH.STA.STNT.ZS", "Prevalenza Stunting (Sottopeso < 5 anni)"),
        (db_id, "SH.STA.OWGH.ZS", "Prevalenza Overweight (> 5 anni)"),
        (db_id, "SI.POV.GINI", "Indice di Gini"),
        (db_id, "GB.XPD.RSDV.GD.ZS", "Spesa in R&S (% del PIL)"),
        (db_id, "EG.ELC.ACCS.ZS", "Accesso all'elettricità (%)"),
        (3, "GOV_WGI_GE.SC", "Efficacia del Governo (Score)"),
        (3, "GOV_WGI_PV.SC", "Stabilità Politica (Score)"),
        (db_id, "MS.MIL.XPND.GD.ZS", "Spesa Militare (% del PIL)"),
        (db_id, "LP.LPI.OVRL.XQ", "Logistics Performance Index")
    ]

    # Ricaviamo una lista dal dataset già ordinato di Pascuzzi
    df = pd.read_csv("./indicators/participants/giuseppe.csv", skipinitialspace=True, sep=";")
    df.columns = ["Categoria", "Codice_indicatore", "Nome_indicatore", "Breve_descrizione", "Database", "Dbid"]
    giuseppe = []
    for i in df.index:
        db_id = str(df.loc[i, "Dbid"])
        db_id = int(db_id[0])
        code = str(df.loc[i, "Codice_indicatore"]).strip()
        description = df.loc[i, "Breve_descrizione"]
        giuseppe.append((db_id, code, description))

    # Creiamo una lista unitaria
    series = list()
    participants = [alessio, luisa, santina, alessia, stefano, gianni, giuseppe]
    for participant in participants:
        for item in participant:
            series.append(item)

    # Mettiamo le serie in un dataset in modo da gestire facilmente gli eventuali duplicati
    df = pd.DataFrame(series)
    df.columns = ["db_id", "code", "description"]
    df.drop_duplicates(subset="code", keep="first", inplace=True)
    df.to_csv("./indicators.csv", header=True, index=False, encoding="utf-8")

    # Riconvertiamo in una lista di tuple
    series = []
    for i in df.index:
        tup = tuple(df.loc[i, :])
        series.append(tup)
    series = sorted(series, key=lambda x: x[1], reverse=False)

    # Controlliamo che sia tutto in ordine
    for s in series:
        print(s)

    # Ciclo resiliente a chiusure di connessione impreviste da parte del server
    # Nel caso di riavvio manuale, riprende dal primo paese NON salvato su disco
    years = range(1960, 2020)
    olympic_countries = list_olympic_countries(warning=True)
    max_iterations = 0
    pause = 10

    for code, country in olympic_countries:

        print(code + "...")
        done = False
        iteration = 0
        file_path = INDICATORS + "/" + code + ".csv"

        if not os.path.exists(file_path):
            t1 = time.time()
            while not done:
                try:
                    download_series(code, series, years, output_csv=file_path)
                    print("Done:", time.time() - t1, "seconds\n")
                    iteration = 0
                    done = True

                except requests.exceptions.ConnectionError as e:
                    print("Connection Error", e)
                    if iteration == max_iterations:
                        done = True
                        iteration = 0
                        continue
                    else:
                        iteration += 1
                        time.sleep(pause)

                except urllib3.exceptions.ProtocolError as e:
                    print("Connection Error", e)
                    if iteration == max_iterations:
                        done = True
                        iteration = 0
                        continue
                    else:
                        iteration += 1
                        time.sleep(pause)

                except Exception as e:
                    print("Connection Error", e)
                    if iteration == max_iterations:
                        done = True
                        iteration = 0
                        continue
                    else:
                        iteration += 1
                        time.sleep(pause)

            # Ritardo casuale per simulare un'interazione più "umana" con il server
            seconds = random.randint(2, 7)
            time.sleep(seconds)

        else:
            print("Already have " + code + "\n")

if __name__ == "__main__":
    main()