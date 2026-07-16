import os
import pandas as pd
from ac.io import Files
from ac.reports import Report
from pandas import DataFrame

def main():
    rerun = True

    # Concateniamo tutti i dataframe dei singoli paesi per stabilire
    # quanti valori null ci sono nel complesso
    if not os.path.exists('research/general.csv') or rerun:
        general = DataFrame()
        for file in Files.iter_all_files(root="./indicators/wb", supported_files=(".csv",), subdir=False):
            print(file, "...")
            df = pd.read_csv(file)
            general = pd.concat([general, df], ignore_index=True, axis=0)

        print("Aspetto del dataset generale")
        print(general.head())

        # Eliminazione colonna "Year"
        general = general.iloc[:, 1:]
        general.to_csv("./research/general.csv", index=False, header=True)
    else:
        general = pd.read_csv("research/general.csv")

    # Questo è il nuovo dataframe in cui si salveranno i conteggi dei valori
    # nulli per ogni indicatore
    df = DataFrame()

    # Scorriamo le colonne del dataframe: per ognuna si contano i valori nulli
    for col in general.columns:
        null = round(general[col].isnull().sum() / len(general) * 100, 2)

        # Si creano in df delle colonne nuove in cui si marca ogni indicatore:
        # si pone una X se è da eliminare, un - se è molto sparso, un + se va bene. Vedi sotto
        mark = ["", "", ""]
        if null < 30:
            mark[2] = "+"
        elif 30 < null < 50:
            mark[1] = "-"
        else:
            mark[0] = "X"
        df[col] = [str(null) + "%", mark[0], mark[1], mark[2]]

    # Le colonne ricevono un nome. Il codice dell'indicatore diventa l'indice
    df = df.T
    df.columns = ["Nulls", "Drop", "Maybe", "Keep"]
    df.index.name = "Indicator"
    df.to_csv("./research/nulls.csv", index=True, header=True)

    text = (
        "In questo semplice report ho concatenato tutti i dataset di tutti gli stati disponibili."
        " In questa maniera ho stimato, all'ingrosso, quanti valori mancano nel complesso: % di valori nulli sul totale."
        " Emerge chiaramente che ci sono dei forti problemi e che la maggior parte degli indicatori non sono utilizzabili."
        "Con la 'X' sono marcati gli indicatori che vanno chiaramente soppressi, "
        "con '-' gli indicatori di scarsa qualità, con '+' quelli accettabili."
        " I dati appaiono essere di scarsissima qualità, nel complesso."
    )

    report = Report()
    report.set(source=df, head="Percentuale valori nulli in tutti i dataset")
    report.headline("Analisi valori nulli\nnegli indicatori socioeconomici")
    report.paragraph("Alessio, 24-5-2026")
    report.paragraph(text)
    report.textualize(justify=["left", "center", "center", "center"], printing=True)
    report.dump(report_name="nulls", extension=".pdf")

if __name__ == "__main__":
    main()


