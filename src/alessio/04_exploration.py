import pandas as pd
import seaborn as sns
from ac.reports import Report
from matplotlib import pyplot as plt
from pandas import DataFrame

df = pd.read_csv("./data/dataset_final_summer.csv")

# Togliamo le righe delle Olimpiadi Invernali
rerun = False
if rerun:
    to_drop = []
    for i in df.index:
        edition = df.loc[i, "edition"]
        if "Winter" in edition:
            to_drop.append(i)
    df.drop(to_drop, axis=0, inplace=True)
    df.to_csv("./data/dataset_final_summer.csv", index=False)

df["edition_id"] = df["edition_id"].astype(str)
df.info()

# Produciamo un po' di mappe
# Consideriamo solo le colonne numeriche degli indicatori: escludiamo
# le colonne delle medaglie
FROM_COLUMN = 10
rerun = False
if rerun:
    country_codes = ["BRA", "FRA", "GER", "GBR", "ITA", "USA", "VEN"]
    for code in country_codes:
        country = df[df["country_noc"] == code]
        corr = country.iloc[:, FROM_COLUMN:].select_dtypes("number").corr()
        plt.figure(figsize=(20,20))
        plt.title(f"{code} correlation")
        sns.heatmap(corr, annot=True, cmap="coolwarm")
        plt.savefig(f"./images/correlation/{code}_corr.png")
        plt.show()
        plt.close()

# Calcoliamo il grado di correlazione medio per ogni indicatore
# Consideriamo solo le colonne numeriche degli indicatori: escludiamo
# le colonne delle medaglie
indicators = index=df.iloc[:, FROM_COLUMN:].select_dtypes("number").columns
country_codes = df["country_noc"].unique()

summary_df = DataFrame(index=indicators, columns=country_codes)
for code in country_codes:
    # Costruiamo un dataframe che incapsula, per ogni riga,
    # la correlazione di un indicatore con tutti gli altri.
    # Ripetiamo per ogni paese
    country = df[df["country_noc"] == code]
    corr = country.iloc[:, FROM_COLUMN:].select_dtypes("number").corr()

    # Appiattiamo il dataframe della correlazione: vogliamo il valor medio
    # di tutte le correlazioni
    corr = corr.abs().mean(axis=1)
    print(f"\n{code} correlation:")
    print(corr)

    # Otteniamo una colonna per ogni paese; le righe sono gli indicatori
    # Corr non è uno scalare, ma una Series
    summary_df[code] = corr

# Nella tabella teniamo solo la colonna del valor medio generale, non quelli per paese
summary_df["Avg. Corr."] = summary_df.mean(axis=1)
columns_to_drop = summary_df.columns[:-1]
summary_df.drop(columns_to_drop, axis=1, inplace=True)

# Calcoliamo quali indicatori devono essere eliminati a seconda della soglia
summary_df["Drop 0.70"] = ""
summary_df["Drop 0.75"] = ""
for i in summary_df.index:
    corr = float(summary_df.loc[i, "Avg. Corr."])
    if corr > 0.7:
        summary_df.loc[i, "Drop 0.70"] = "X"
    if corr > 0.75:
        summary_df.loc[i, "Drop 0.75"] = "X"

# Generiamo un report
report = Report()
report.set(summary_df, head="Indicator average correlation with each other")
report.textualize(justify=["center", "center", "center"])
report.paragraph("Suggested: drop indicator with a correlation level >= 0.75")
report.dump(report_name="correlation", extension="pdf")

# Eliminiamo gli indicatori troppo correlati dal dataset originale
keep = ["SP.POP.TOTL", "NY.GDP.MKTP.CD"]
indicators_to_drop = []
for i in summary_df.index:
    threshold = summary_df.loc[i, "Drop 0.75"]
    if threshold == "X" and i not in keep:
        print("Deleted:", i)
        indicators_to_drop.append(i)

# Salviamo il dataset "potato" in un alto csv
df.drop(indicators_to_drop, axis=1, inplace=True)

# Trasformiamo l'anno in numero
for i in df.index:
    year = str(df.loc[i, "edition"])
    df.loc[i, "edition"] = int(year[:4])

df["edition"] = df["edition"].astype(int)
df.to_csv("./data/dataset_final_summer_capped.csv", index=False, header=True, encoding="utf-8")

