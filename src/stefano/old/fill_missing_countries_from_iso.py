from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

MAIN_CSV_PATH = PROJECT_ROOT / "output" / "olympic_medals_with_socioeconomic_indicators_3.csv"
MISSING_CODES_LOG_PATH = PROJECT_ROOT / "output" / "missing_iso_codes.txt"

# Primary location requested by the exercise, plus a fallback matching this repo layout.
ISO_CSV_CANDIDATES = (
    SCRIPT_DIR / "ISO.csv",
    PROJECT_ROOT / "output" / "ISO.csv",
)


def find_iso_csv_path() -> Path:
    """Return the first available ISO.csv path."""
    for path in ISO_CSV_CANDIDATES:
        if path.exists():
            return path

    searched_paths = ", ".join(str(path) for path in ISO_CSV_CANDIDATES)
    raise FileNotFoundError(f"ISO.csv non trovato. Percorsi controllati: {searched_paths}")


def validate_columns(dataframe: pd.DataFrame, required_columns: set[str], csv_path: Path) -> None:
    """Fail clearly if an input CSV does not contain the expected columns."""
    missing_columns = required_columns - set(dataframe.columns)
    if missing_columns:
        missing_text = ", ".join(sorted(missing_columns))
        raise ValueError(f"Colonne mancanti in {csv_path}: {missing_text}")


def normalize_code(series: pd.Series) -> pd.Series:
    """Normalize ISO/NOC codes for case-insensitive and trim-insensitive matching."""
    return series.astype("string").str.strip().str.upper()


def country_is_missing(series: pd.Series) -> pd.Series:
    """Find null, NaN-like, empty, and whitespace-only country values."""
    normalized_country = series.astype("string").str.strip()

    return (
        normalized_country.isna()
        | normalized_country.eq("")
        | normalized_country.str.upper().isin({"NAN", "NULL"})
    )


def build_iso_lookup(iso_dataframe: pd.DataFrame) -> pd.Series:
    """Build a Series mapping alpha-3 country codes to country names."""
    iso_codes = normalize_code(iso_dataframe["alpha-3"])
    iso_names = iso_dataframe["name"].astype("string").str.strip()

    iso_lookup = pd.Series(iso_names.to_numpy(), index=iso_codes)
    #iso_lookup = iso_lookup[iso_lookup.index.notna() & iso_lookup.index.ne("")]
    iso_lookup = iso_lookup[iso_lookup.index.notna() & (iso_lookup.index != "")]
    iso_lookup = iso_lookup[iso_lookup.notna() & iso_lookup.ne("")]

    return iso_lookup[~iso_lookup.index.duplicated(keep="first")]


def fill_missing_countries(main_csv_path: Path, iso_csv_path: Path) -> tuple[int, list[str]]:
    """Fill missing country values from ISO alpha-3 codes and return summary data."""
    medals_dataframe = pd.read_csv(main_csv_path, dtype="string", keep_default_na=False)
    iso_dataframe = pd.read_csv(iso_csv_path, dtype="string", keep_default_na=False)

    validate_columns(medals_dataframe, {"country", "country_noc"}, main_csv_path)
    validate_columns(iso_dataframe, {"alpha-3", "name"}, iso_csv_path)

    missing_country_mask = country_is_missing(medals_dataframe["country"])
    normalized_country_noc = normalize_code(medals_dataframe["country_noc"])
    iso_lookup = build_iso_lookup(iso_dataframe)

    mapped_country_names = normalized_country_noc.map(iso_lookup)
    rows_to_update = missing_country_mask & mapped_country_names.notna() & mapped_country_names.ne("")

    medals_dataframe.loc[rows_to_update, "country"] = mapped_country_names.loc[rows_to_update]

    missing_iso_mask = (
        missing_country_mask
        & normalized_country_noc.notna()
        & normalized_country_noc.ne("")
        & (mapped_country_names.isna() | mapped_country_names.eq(""))
    )
    missing_iso_codes = sorted(normalized_country_noc.loc[missing_iso_mask].dropna().unique().tolist())

    medals_dataframe.to_csv(main_csv_path, index=False)

    return int(rows_to_update.sum()), missing_iso_codes


def write_missing_codes_log(log_path: Path, missing_iso_codes: list[str]) -> None:
    """Write one missing country_noc code per line."""
    log_text = "\n".join(missing_iso_codes)
    if log_text:
        log_text += "\n"

    log_path.write_text(log_text, encoding="utf-8")


def main() -> None:
    iso_csv_path = find_iso_csv_path()
    updated_count, missing_iso_codes = fill_missing_countries(MAIN_CSV_PATH, iso_csv_path)
    write_missing_codes_log(MISSING_CODES_LOG_PATH, missing_iso_codes)

    print(f"Country aggiornati: {updated_count}")
    print(f"Codici ISO non trovati: {len(missing_iso_codes)}")


if __name__ == "__main__":
    main()
