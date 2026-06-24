import re
import requests
from bs4 import BeautifulSoup
from ftfy import fix_text
from pandas import DataFrame
from ac.utils import random_delay


URL_REPUBBLICA_SEARCH = (
    "https://ricerca.repubblica.it/ricerca/repubblica-it?"
    "query=scherma+olimpiadi+italia&fromdate=2000-01-01"
    "&todate=2026-06-21&sortby=adate&author=&mode=all"
)


def clean_title(title:str):
    clean = ""
    for char in title:
        if char.isalnum():
            clean += char
        else:
            clean += " "
    return clean


def drop_articles(soup: BeautifulSoup, data:list):
    
    """
    Scarichiamo gli articoli della pagina corrente. I link agli articoli sono contenuti nei tag "article".
    Ecco un esempio:

    <div class="contA">
          <section id="lista-risultati">
           <!-- risultati -->
           <article>
            <h1>
             <a href="http://www.repubblica.it/online/sport/sidney/sidney/sidney.html?ref=search" title="Leggi l'articolo">
              In 361 alle Olimpiadi
    """
    
    articles = soup.find_all("article")
    for article in articles:

        # Troviamo il link all'articolo dalla pagina dei risultati della ricerca
        a = article.find("a")
        href = a.attrs["href"]
        print(a.text, href)

        # Recuperiamo titolo e data dell'articolo
        title = a.text.strip()
        try:
            date = re.findall(pattern=r"\d\d\d\d/\d\d/\d\d", string=str(href))[0]
            date = date.replace("/", "-")
        except Exception as e:
            print("Error parsing date:", e)
            date = "0000-00-00"

        # Apriamo il link dell'articolo
        response = requests.get(str(href))
        soup = BeautifulSoup(response.content, "html.parser")

        # Cerchiamo il tag in cui è contenuto il full text
        full = soup.find("div", class_="articolo")
        if full is None:
            full = soup.find("div", class_="story__text")
        if full is None:
            full = soup.find("body")

        # Salviamo su disco l'articolo dopo aver ripulito per bene il testo
        path = "./repubblica/" + date + "_" + clean_title(title) + ".txt"
        with (open(path, "w") as f):
    
            clean = full.text.strip()
            clean = clean.replace("\t", "\n")
            clean = clean.replace("\r", "\n")
            
            while "\n\n" in clean:
                clean = clean.replace("\n\n", "\n")
            while "  " in clean:
                clean = clean.replace("  ", " ")

            clean = fix_text(clean)
            f.write(clean)

            # Salviamo tutto anche in una lista per creare successivamente un dataset
            data.append((title, date, str(href), clean))


def next_page(soup: BeautifulSoup):
    """
    Carica la pagina successiva cercando il link "Successiva".
    Se non ce ne sono più, restituisce None
    """
    tags = soup.find_all("a")
    for tag in tags:
        label = tag.text.strip().lower()
        if "successiva" in label and len(label.split()) == 1:
            response = requests.get(tag.attrs["href"])
            return BeautifulSoup(response.content, "html.parser")
    return None


def main():

    articles = []
    response = requests.get(URL_REPUBBLICA_SEARCH)
    soup = BeautifulSoup(response.content, "html.parser")
    drop_articles(soup, articles)

    # Ora passiamo ad aprire le pagine della ricerca cercando il link "successiva"
    page = next_page(soup)
    while page is not None:
        drop_articles(page, articles)
        random_delay(milliseconds=2000, delta=500)
        page = next_page(page)

    # Salviamo tutto in un dataset
    df = DataFrame.from_records(articles, columns=["title", "date", "href", "text"])
    df.to_csv("./repubblica/repubblica_df.csv", header=True, sep="§", encoding="utf-8")


if __name__ == "__main__":
    main()