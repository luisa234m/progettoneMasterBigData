import time
import warnings

import pandas as pd
from pandas import DataFrame
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler

from ac.io import Files

# Stabiliamo quali indicatori sono da eliminare. Nel dataset null.csv
# il codice degli indicatori costituisce la colonna "Indicator"

nulls = pd.read_csv("./research/nulls.csv")
to_drop = nulls[nulls["Drop"] == "X"]["Indicator"].tolist()

# Apriamo ogni file csv relativo a ogni singolo paese, eliminiamo gli indicatori
# superflui e salviamo il file ridotto con lo stesso nome nel percorso "/clean"

try:
    for file in Files.iter_all_files("./indicators/wb", supported_files=[".csv"], subdir=False):
        df = pd.read_csv(file)
        df.drop(labels=to_drop, axis=1, inplace=True)
        new_file = "./indicators/clean/" + file.name
        print(new_file)
        df.to_csv(new_file, index=False)
except KeyError:
    print("File già processati")

# Ora costruiamo un dataset unitario dopo aver effettuato una compressione tramite pca.
# In realtà se ne costuiscono due: uno con i dati normalizzati e uno con i dati originali.

aggregate_pca = DataFrame(index=[year for year in range(1960, 2020)])
aggregate_scaled = DataFrame(index=[year for year in range(1960, 2020)])
aggregate_scaled.index.name = aggregate_pca.index.name = "Year"
warnings.filterwarnings("ignore")

for file in Files.list_all_files("./indicators/clean", supported_files=[".csv"], subdir=False):
    print(file.name, "...")
    df = pd.read_csv(file)
    df.fillna(0.0, inplace=True)
    df.drop(labels=["Year"], axis=1, inplace=True)

    # PCA su dati non normalizzati
    pca = PCA(n_components=1)
    aggregate_pca[file.name.replace(".csv", "")] = pca.fit_transform(df.values)

    # PCA su dati normalizzati
    minmax = MinMaxScaler()
    scaled = minmax.fit_transform(df.values)
    pca = PCA(n_components=1)
    aggregate_scaled[file.name.replace(".csv", "")] = pca.fit_transform(scaled)
    time.sleep(0.02)

# Si salvano i due dataset
aggregate_pca.to_csv("./indicators/aggregate/pca.csv", index=True)
aggregate_scaled.to_csv("./indicators/aggregate/pca_scaled.csv", index=True)
