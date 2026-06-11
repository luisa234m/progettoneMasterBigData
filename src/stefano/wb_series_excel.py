import re
import pandas as pd
import wbgapi as wb


OUTPUT_FILE = "../../data/xlsx_pptx/world_bank_series.xlsx"
DATABASES_SHEET_NAME = "databases"


def safe_sheet_name(name: str, fallback: str) -> str:
    cleaned = re.sub(r"[\[\]\:\*\?\/\\]", "_", str(name)).strip()
    cleaned = cleaned[:31]
    return cleaned or fallback


def unique_sheet_name(name: str, used: set) -> str:
    base = name[:31]
    candidate = base
    i = 1

    while candidate in used:
        suffix = f"_{i}"
        candidate = base[: 31 - len(suffix)] + suffix
        i += 1

    used.add(candidate)
    return candidate


def main():
    sources = list(wb.source.list())

    used_sheet_names = set()

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        # Sheet con la lista di tutti i database
        databases_df = pd.DataFrame(sources)
        databases_df.to_excel(
            writer,
            sheet_name=DATABASES_SHEET_NAME,
            index=False
        )
        used_sheet_names.add(DATABASES_SHEET_NAME)

        # Uno sheet per ogni database/source
        for source in sources:
            source_id = source["id"]
            source_name = source["name"]

            print(f"Elaboro database {source_id}: {source_name}")

            raw_sheet_name = f"{source_id}_{source_name}"
            sheet_name = safe_sheet_name(
                raw_sheet_name,
                f"source_{source_id}"
            )
            sheet_name = unique_sheet_name(sheet_name, used_sheet_names)

            try:
                series = list(wb.series.list(db=source_id))

                if series:
                    df = pd.DataFrame(series)
                else:
                    df = pd.DataFrame([{
                        "source_id": source_id,
                        "source_name": source_name,
                        "message": "Nessuna serie trovata"
                    }])

            except Exception as e:
                df = pd.DataFrame([{
                    "source_id": source_id,
                    "source_name": source_name,
                    "error": str(e)
                }])

            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"File creato: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()