import json
import pandas as pd
import re
from ftfy import fix_text


def date_in_doc(text:str):
    pattern = r"\(\d+°* \w+ \d\d\d\d\)"
    return re.findall(pattern, text)[0][1:-1]


def month_from_text(month:str):
    match month.lower():
        case "gennaio": return "01"
        case "febbraio": return "02"
        case "marzo": return "03"
        case "aprile": return "04"
        case "maggio": return "05"
        case "giugno": return "06"
        case "luglio": return "07"
        case "agosto": return "08"
        case "settembre": return "09"
        case "ottobre": return "10"
        case "novembre": return "11"
        case _: return "12"


def standard_date_format(text:str):
    day, month, year = text.split(" ")
    month = month_from_text(month)
    return year + "-" + month + "-" + day


def main():
    repubblica = pd.read_csv("./repubblica/repubblica_df.csv", sep="§", encoding="utf-8")
    to_keep = []
    total = len(repubblica)

    for i, row in repubblica.iterrows():
        title = str(row.loc["title"])
        date  = str(row.loc["date"])
        doc   = str(row.loc["text"])
        url   = str(row.loc["href"])

        # Fixing the date
        if date.startswith("0000"):
            try:
                date = date_in_doc(doc)
                date = standard_date_format(date)
            except Exception as e:
                print("\nData non trovata:", e)
                print(f"Articolo {i} di {total}\n")
                date = "0000-00-00"

        # Getting rid of the non relevant texts
        occurrences = [i for i in range(len(doc)) if doc.startswith("\n", i)]
        if len(occurrences) < 100:

            # Fixing the text and the title
            text = fix_text(doc).replace("\n", " ")
            title = fix_text(title).replace("\n", " ")
            item = {"title": title, "date": date, "text": text, "url": url}
            to_keep.append(item)

        print(f"Fatti {i} di {total}")

    with open("repubblica/repubblica_clean.json", "w", encoding="utf-8") as f:
        to_keep = sorted(to_keep, key=lambda k: k["date"])
        json.dump(to_keep, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
