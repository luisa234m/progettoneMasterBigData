import json
from copy import deepcopy
from pandas import DataFrame
from ac.llm import SmallAgent
from ac.utils import Configuration


PROMPT_TRANSLATE = """Sei un traduttore professionista. Traduci il contenuto del tag <source> in inglese.
Non aggiungere commenti o spiegazioni."""


def build_prompt(text_to_translate:str):
    return PROMPT_TRANSLATE + " <source> " + text_to_translate + " </source>"


def main():
    config = Configuration()
    agent = SmallAgent(**config("llama_small"))
    print(config("llama_small/n_ctx"))
    articles_it = DataFrame(data=json.load(open("./repubblica/repubblica_clean.json")))
    articles_en = deepcopy(articles_it)

    for i, row in articles_it.iterrows():
        if i % 10 == 0 and i != 0:
            agent.delete()
            agent = SmallAgent(**config("llama_small"))
        print("Done", i, "out of", len(articles_it))
        text_it = row["text"]
        agent.send(build_prompt(text_it), mode="user")
        text_en = agent.ask(max_tokens=config("llama_small/n_ctx"))
        print(text_en)
        print()
        articles_en.loc[i, "text"] = text_en.replace("<source>", "").replace("</source>", "")

    articles_en.to_json("./repubblica/repubblica_clean_en.json", indent=4)
    for article in articles_en["text"][0:10]:
        print(str(article))
        print("\n\n")


if __name__ == "__main__":
    main()