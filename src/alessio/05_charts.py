import pandas as pd
from matplotlib import pyplot as plt
from wb_utils import WbIndicators

df = pd.read_csv("./data/dataset_final_summer_capped.csv")
country_codes = ["USA", "GER", "ITA", "FRA", "BRA", "VEN"]
indicators = df.iloc[:, 10:].select_dtypes("number").columns
wbd = WbIndicators()

for indicator in indicators:
    print(indicator)
    plt.figure(figsize=(19, 10))
    plt.title(wbd.description(indicator) + " - " + indicator)
    for country_code in country_codes:
        country = df[df["country_noc"] == country_code]
        country = country.sort_values(by="edition", ascending=True)
        time_series = country[indicator]
        time_series.fillna(time_series.mean(), inplace=True)
        plt.plot(country["edition"], time_series, label=country_code)
        plt.scatter(country["edition"], time_series)
    plt.legend()
    plt.savefig("./images/timeseries/" + indicator.replace(".", "_") + ".png")
    plt.show()
    plt.close()

print("----------------")
print(wbd.code(keywords=["neonatal"]))