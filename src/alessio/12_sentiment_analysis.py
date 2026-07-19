import altair as alt
import json
import os.path
import pandas as pd
from altair import Chart
from matplotlib import pyplot as plt
from pandas import DataFrame
from ac.llm import SentimentAnalyzer, Chunking
from ac.ml.clustering import ClusterMaker
from ac.reports import Report
from ac.utils import config, registry


def main():
    Chunking.setup(**config("chunker"))

    rerun = True
    if not os.path.exists("repubblica/repubblica_emotions.json") or rerun:
        articles = DataFrame(data=json.load(open("./repubblica/repubblica_clean_en.json", "r", encoding="utf-8")))
        analyzer = SentimentAnalyzer(**config("sentiment_analysis"))
        articles = analyzer(articles["text"].to_list(), articles)
        articles.to_json("./repubblica/repubblica_emotions.json", indent=4)

        data = json.load(open("repubblica/repubblica_emotions.json", "r", encoding="utf-8"))
        articles = DataFrame(data=data)
        ranking_emotions = DataFrame(articles.select_dtypes("number").mean().sort_values(ascending=False))
        ranking_emotions.reset_index(inplace=True)
        ranking_emotions.columns = ["emotion", "score %"]
        ranking_emotions.set_index("emotion", inplace=True)
        ranking_emotions["score %"] = ranking_emotions["score %"] * 100

        registry(name="ranking_emotions", obj=ranking_emotions)
        Report.pipeline("./config/report_emotions.yaml")

        ranking_emotions = ranking_emotions.iloc[1:11, :]
        ranking_emotions.reset_index(inplace=True)
        ranking_emotions.columns = ["emotion", "score %"]
        Chart(ranking_emotions)\
        .mark_bar(size=30)\
        .encode(
            x=alt.X(shorthand="emotion:N", axis=alt.Axis(title="Emozioni"), sort="-y"),
            y=alt.Y(shorthand="score %:Q", axis=alt.Axis(title="Punteggio in %")),
            color=alt.Color(shorthand="emotion:N", scale=alt.Scale(scheme="tableau10"))
        )\
        .properties(
            title="Le 10 emozioni con punteggi più alti",
            width=600,
            height=400
        )\
        .configure(
            padding={
                "left": 20,
                "right": 20,
                "top": 20,
                "bottom": 20
            }
        )\
        .configure_axis(
            titleFontSize=14,
            labelFontSize=12
        )\
        .configure_title(fontSize=16)\
        .configure_legend(titleFontSize=14, labelFontSize=14)\
        .save("./images/emotions.png")

    # Scatterplots
    data = json.load(open("repubblica/repubblica_emotions.json", "r", encoding="utf-8"))
    articles = DataFrame(data=data)
    articles = articles[articles["date"] != "0000-00-00"]
    articles["date"] = pd.to_datetime(articles["date"], format="%Y-%m-%d")
    articles.plot(kind="scatter", x="date", y="disapproval")
    articles.plot(kind="scatter", x="date", y="approval")
    plt.show()

    articles["enthusiasm"] = (articles["approval"] + articles["admiration"]).clip(0, 1)
    articles["date_int"] = articles["date"].map(lambda x: x.toordinal())
    
    ClusterMaker(
        method="hdbscan",
        data=articles,
        subset=["date_int", "enthusiasm"],
        export="clustering",
    )\
    .fit(min_samples=5, min_cluster_size=10)\
    .draw(
        what="clustering",
        centroids=True,
        x="date_int",
        y="enthusiasm",
        title="HDBSCAN degli articoli per 'enthusiasm'",
        figsize=(10, 6),
        show=True,
        save="./images/fetching_enthusiasm_hdbscan.png"
    )

    ClusterMaker(
        method="kmeans",
        data=articles,
        subset=["date_int", "enthusiasm"],
        export="clustering",
    )\
    .explore()\
    .fit()\
    .draw(
        what="clustering",
        centroids=True,
        x="date_int",
        y="enthusiasm",
        title="KMEANS degli articoli per 'enthusiasm'",
        figsize=(10, 6),
        show=True,
        save="./images/fetching_enthusiasm_kmeans.png"
    )


if __name__ == "__main__":
    main()