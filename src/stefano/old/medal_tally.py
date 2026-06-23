import pandas as pd
from pandas import DataFrame

general = pd.read_csv('./data/Olympic_Medal_Tally_History.csv')
summer_editions = []

# Selezioniamo solo i dati relativi ai Giochi estivi
for i in general.index:
    edition = str(general.loc[i, "edition"]).lower()
    if "summer" in edition:
        summer_editions.append(general.loc[i, :].values.tolist())
summer_df = pd.DataFrame(summer_editions)
summer_df.columns = ["edition","edition_id","year","country","country_noc","gold","silver","bronze","total"]

# Puliamo il campo edition in modo da trasformarlo in un campo intero
for i in summer_df.index:
    edition = str(summer_df.loc[i, "edition"])
    edition = edition[:4]
    summer_df.loc[i, "edition"] = int(edition)
summer_df["edition"] = summer_df["edition"].astype(int)
summer_df.to_csv('./data/summer.csv', index=False, header=True, encoding="utf-8")

