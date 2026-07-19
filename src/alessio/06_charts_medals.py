import matplotlib.pyplot as plt
import pandas as pd
from ac.reports import Report
from wb_utils import WbIndicators

def main():
    wb = WbIndicators()
    df = pd.read_csv("./data/dataset_final_summer_capped.csv")
    df["total"] = df["total"].astype(int)
    df = df[df["edition"] < 1980]

    report = Report()

    i = 1
    for indicator in sorted(wb.indicators()):

        plt.figure(figsize=(19,10))
        plt.title(f"Total medals w.r.t {wb.description(indicator)} - {indicator}")
        plt.ylabel("Medals")
        plt.xlabel(indicator)
        plt.scatter(df[indicator], df["total"])
        plt.savefig(f"./images/scatter/medals_{indicator}.png")
        plt.show()
        plt.close()

        report.set(
            source=df[["total", indicator]].corr(),
            head=f"Correlation medals w.r.t.\n{wb.description(indicator)}\n{indicator}"
        )
        report.textualize()
        if i % 5 == 0:
            report.new_page()

        i += 1

    report.dump(report_name="correlation_medals_early", extension="pdf")

if __name__ == "__main__":
    main()