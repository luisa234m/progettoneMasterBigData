import json
import pandas as pd
from ac.llm import SmartSearch, SmallAgent
from ac.reports import Report
from ac.utils import Configuration
from pandas import DataFrame

TOP_K = 40

def main():

    # Prova di Configurator
    config = Configuration()

    # Loading the texts as a DataFrame
    data = json.load(open("./repubblica/repubblica_clean.json", "r", encoding="utf-8"))
    repubblica = DataFrame(data=data, columns=["title", "date", "text", "url"])
    repubblica.sort_values(by="date", inplace=True)

    # Defining a query and retrieving the most relevant articles
    search = SmartSearch(**config("smart_search"))
    search.feed(repubblica["text"].tolist())
    query = "Quali articoli parlano dei successi dell'Italia nella scherma?"
    results = search.semantic(query=query, top_k=TOP_K)

    # Displaying and saving the results
    n_token = 0
    selection = DataFrame(columns=["title", "date", "text", "url"])
    for result in results:
        _, doc, score = result
        n_token += len(doc.split(" "))
        print(score, " --- ", doc[:100])
        row = repubblica[repubblica["text"] == doc]
        selection = pd.concat([selection, row], ignore_index=True, axis=0)
    selection.to_json("./repubblica/query_1.json", indent=4)

    print("\n-----------------------")
    print("N token: ", int(1.5 * n_token))     # Approximately, the token number found by the LLM
    print("-----------------------\n")

    # Asking the LLM and saving the answer
    print("Carico Llama; attendi una ventina di secondi...")
    agent = SmallAgent(**config("llama_small"))

    print("Do i documenti a Llama...")
    agent.rag(documents=selection["text"].tolist())
    prompt = "Rispondi alla domanda dell'utente in maniera sintetica e per punti"
    agent.send(prompt, mode="system")

    print("Ora rispondo alla domanda...")
    prompt = "Quali sono i maggiori successi dell'Italia nella scherma?"
    agent.send(prompt, mode="user")
    answer = agent.ask(max_tokens=512)

    # Saving the query result in a pdf document
    report = Report()
    report.headline(prompt)
    report.paragraph(answer)
    print(report)
    report.dump(report_name="risultati_scherma_italia", extension="pdf")

    # Second query
    query = "Quali articoli spiegano le ragioni dei successi dell'Italia nella scherma?"
    results = search.semantic(query=query, top_k=TOP_K)

    # Displaying the results
    n_token = 0
    selection = DataFrame(columns=["title", "date", "text", "url"])
    for result in results:
        _, doc, score = result
        n_token += len(doc.split(" "))
        print(score, " --- ", doc[:100])
        row = repubblica[repubblica["text"] == doc]
        selection = pd.concat([selection, row], ignore_index=True, axis=0)
    selection.to_json("./repubblica/query_2.json", indent=4)

    print("\n-----------------------")
    print("N token: ", int(1.5 * n_token))  # Approximately, the token number found by the LLM
    print("-----------------------\n")

    # Asking the LLM and saving the answer
    print("Do i documenti a Llama...")
    agent.rag(documents=selection["text"].tolist())
    prompt = """Rispondi alla domanda dell'utente con un testo continuo e articolato. 
                Non rispondere in maniera schematica.
                Cita nomi di personaggi importanti relativi all'argomento trattato, se ce ne sono;
                se essi hanno ottenuto risultati importanti, fai qualche esempio.
                Produci un testo di almeno 500 parole."""

    print("Ora rispondo alla domanda...")
    agent.send(prompt, mode="system")
    prompt = "Quali sono le cause dei successi dell'Italia nella scherma?"
    agent.send(prompt, mode="user")
    answer = agent.ask()

    # Saving the query result in a pdf document
    report = Report()
    report.headline(prompt)
    report.paragraph(answer)
    print(report)
    report.dump(report_name="ragioni_successi_italia", extension="pdf")


if __name__ == "__main__":
    main()