import pandas as pd
from ac.io import Files
from ac.nlp import TextStats

"""
df = pd.read_csv("./repubblica/repubblica_df.csv", encoding="utf-8", sep="§")
df.columns.names.values = ["title", "date", "href", "text"]
df.drop_duplicates(subset="text", keep="first", inplace=True)
print(df.head(20))
"""

paths = Files.list_all_files(root="./repubblica", supported_files=[".txt"])
texts = []
for path in paths:
    with open(path, "r", encoding="utf-8") as f:
        texts.append(f.read())

stats = TextStats(language="italian", texts=texts, auto=True)
stats.wordcloud(dir_path="./repubblica", title="scherma")