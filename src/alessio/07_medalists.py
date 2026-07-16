import random
import time
from pathlib import Path
import numpy as np
import pandas as pd
from pandas import DataFrame
import wikipediaapi
from transformers import pipeline
from ac.io import Files
from ac.reports import Report


def main():

    rerun = False
    if rerun:
        athletes = pd.read_csv("./data/Olympic_Athlete_Event_Details.csv")
        athletes.dropna(subset=["medal"], inplace=True)
        athletes["medal"] = 1

        drop_winter = []
        for i in athletes.index:
            if "winter" in athletes.loc[i, "edition"].lower():
                drop_winter.append(i)
        athletes.drop(drop_winter, inplace=True)

        athletes.to_csv("./data/olympic_winners.csv", encoding="utf-8", index=False, header=True)
        names = athletes["athlete"].unique()

        winners = DataFrame(index=np.arange(len(names)), columns=["athletes", "medals", "country"])
        for i, athlete in enumerate(names):
            subset = athletes[athletes["athlete"] == athlete]
            medals = subset["medal"].sum()
            winners.loc[i, "medals"] = medals
            winners.loc[i, "athletes"] = athlete
            value = subset.iloc[0, 2]
            winners.loc[i, "country"] = value
            if i % 1000 == 0:
                print("Processed", i, "athletes out of", len(names))

        winners.sort_values(by="medals", inplace=True, ascending=False)
        winners.to_csv("./data/olympic_ranking.csv", encoding="utf-8", index=False, header=True)
        winners[winners["country"] == "ITA"].to_csv("./data/olympic_winners_ita.csv", encoding="utf-8", index=False, header=True)

    else:
        winners = pd.read_csv("./data/olympic_ranking.csv")

    rerun = False
    if rerun:
        wiki = wikipediaapi.Wikipedia(user_agent="Test_Unipi (a.cioli1@studenti.unipi.it)", language='en')

        # Finding the countries having less than 2% of the medals
        all_medals = winners["medals"].sum()
        print("All medals", all_medals)
        threshold = round(0.0001 * all_medals)
        print("Threshold", threshold)
        grouped = winners[["country", "medals"]].groupby("country")
        grouped = grouped["medals"].sum()
        less_developed_countries = grouped[(grouped > 0) & (grouped < threshold)].index
        print(less_developed_countries)

        #less_developed_countries = "AFG, ALB, BEN, BIZ, BUR, BDI, CPV, MLI, NRU, NEP".split(", ")

        for country in less_developed_countries:
            subset = winners[winners["country"] == country]
            if len(subset) > 0:
                subset.to_csv(f"./data/olympic_winners_{country}.csv", encoding="utf-8", index=False, header=True)
                names = subset["athletes"].unique()

                for name in names:
                    try:
                        page = wiki.page(name)
                        print(country, "-", name)
                        print(page.text[:160])
                        print()

                        report = Report()
                        report.headline(name)
                        lines = page.text.split("\n")
                        for line in lines:
                            report.paragraph(line)
                        report.dump(country + "_" + name, extension=".pdf")
                        report.dump(country + "_" + name, extension=".txt")

                        delay = 3 + random.randint(-500, 500) / 1000
                        time.sleep(delay)

                    except Exception as e:
                        print(e)

    rerun = True
    if rerun:
        # Sentiment analysis
        text_analysis = pipeline(
            task="text-classification",
            model="SamLowe/roberta-base-go_emotions",
            top_k=None
        )

        initialized = False
        emotions = []
        sentiment = {}
        for file_path in Files.list_all_files("./reports/txt", supported_files=[".txt"]):
            with open(file_path, "r") as f:
                text = f.read()

            chunks = [text[i:i + 500] for i in range(0, len(text), 500)]

            table = []
            for chunk in chunks:
                scores = text_analysis(chunk)[0]
                results = []
                scores = sorted(scores, key=lambda x: x["label"], reverse=False)
                for score in scores:
                    results.append(score["score"])
                    if not initialized:
                        emotions.append(score["label"])
                table.append(results)
                initialized = True

            df = pd.DataFrame(table)
            key = Path(file_path).name.replace(".txt", "")
            sentiment[key] = df.mean(axis=0).to_list()
            print(key, len(sentiment[key]))

        print(emotions)
        df = DataFrame(index=list(sentiment.keys()), data=list(sentiment.values()))
        df.index.name = "athletes"
        print(df.head())
        df.to_csv("./data/olympic_sentiment.csv", encoding="utf-8", index=True, header=True)
        print(df.head())

    rerun = True
    if rerun:
        sentiment = pd.read_csv("./data/olympic_sentiment.csv")
        sentiment.set_index("athletes", inplace=True)
        sentiment.columns = sorted("anger,fear,disgust,sadness,joy,surprise,disapproval,optimism,nervousness,pride,admiration,disappointment,neutral,annoyance,approval,realization,desire,excitement,embarrassment,confusion,caring,gratitude,love,grief,relief,curiosity,remorse,amusement".split(","), reverse=False)
        sentiment.to_csv("./data/olympic_sentiment.csv")

if __name__ == "__main__":
    main()