from ac.io import Files
from ac.llm import SmallAgent
from ac.reports import Report
from ac.utils import Configuration

PROMPT = """
I testi che ti sono stati dati come contesto sono in lingua inglese 
e contengono biografie di atleti olimpici che hanno vinto medaglie venendo da paesi poveri del mondo o da paesi che, 
comunque, nella storia, non hanno mai ottenuto un alto numero di medaglie. Questi atleti, dunque,
sono delle anomalie storiche. 
Nelle loro biografie esiste qualcosa in comune che possa spiegare il loro successo?
Rispondi alla domanda in italiano scrivendo un testo discorsivo e dettagliato.
Quando possibile, fai degli esempi concreti di storie di atleti a supporto delle tue affermazioni.
"""

HEADLINE = "DALLE STALLE ALLE STELLE"
CAPTION = "Cosa hanno in comune atleti di successo che vengono da paesi sportivamente non di successo"

def main():
    config = Configuration()
    agent = SmallAgent(**config("llama_small"))
    documents = Files.read_all_texts(directory="./reports/txt/outsiders", supported_files=["txt"])
    agent.rag(documents)
    agent.send(PROMPT, mode="user")
    answer = agent.ask()
    Report()\
    .headline(HEADLINE)\
    .caption(CAPTION)\
    .paragraph(answer)\
    .console()\
    .dump("underdog2", "pdf")

if __name__ == "__main__":
    main()