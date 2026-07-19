from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_MAIN_FILENAME = "Olympic_Medal_Tally_History_definitivo.csv"
DEFAULT_GAMES_SUMMARY_FILENAME = "Olympic_Games_Summary.csv"
DEFAULT_CLEAN_DIRNAME = "clean"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"
DEFAULT_YEARS_TO_AGGREGATE = 4

OUTPUT_CSV_NAME = "olympic_medals_with_socioeconomic_indicators_2.csv"
REPORT_NAME = "missing_data_report_2.txt"

HOST_COUNTRY_COLUMN = "paese_olimpiade"
HOST_CITY_COLUMN = "citta_olimpiade"
YEAR_NUMBER_COLUMN = "_year_number"

MAIN_REQUIRED_COLUMNS = {
    "edition",
    "year",
    "country_noc",
    "gold",
    "silver",
    "bronze",
    "total",
}
GAMES_REQUIRED_COLUMNS = {"edition", "country_noc", "city"}
MEDAL_COLUMNS = ("gold", "silver", "bronze", "total")
EXTRA_ROW_FIXED_COLUMNS = {"edition", "year", "country_noc", *MEDAL_COLUMNS}


@dataclass
class CountryIndicators:
    """Prepared socioeconomic indicators for a single country."""

    noc: str
    path: Path
    frame: pd.DataFrame
    indicator_columns: list[str]
    available_years: set[int]


def normalize_noc(value: object) -> Optional[str]:
    """Return a clean country code for lookups, or None for missing values."""
    if pd.isna(value):
        return None

    text = str(value).strip()
    return text if text else None


def parse_year(value: object) -> Optional[int]:
    """Parse a year without changing the original value stored in the data."""
    year = pd.to_numeric(value, errors="coerce")
    if pd.isna(year):
        return None

    return int(year)


def require_columns(frame: pd.DataFrame, required: set[str], source: Path) -> None:
    """Fail fast when an input file misses columns needed by the workflow."""
    missing = required.difference(frame.columns)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"Missing required columns in {source}: {missing_text}")


def expected_previous_years(olympic_year: int, years_to_aggregate: int) -> list[int]:
    """Return the years used to calculate pre-Olympic indicator averages."""
    return list(range(olympic_year - years_to_aggregate, olympic_year))


def load_main_data(main_file: Path) -> pd.DataFrame:
    """Load the medal tally file while keeping all original columns."""
    main_df = pd.read_csv(main_file)
    require_columns(main_df, MAIN_REQUIRED_COLUMNS, main_file)
    return main_df


def load_games_summary(
    games_summary_file: Path, report_lines: list[str]
) -> pd.DataFrame:
    """Load Olympic host country and city, renamed to avoid column collisions."""
    games_df = pd.read_csv(games_summary_file)
    require_columns(games_df, GAMES_REQUIRED_COLUMNS, games_summary_file)

    duplicated_editions = (
        games_df.loc[games_df["edition"].duplicated(), "edition"]
        .dropna()
        .astype(str)
        .unique()
    )
    for edition in sorted(duplicated_editions):
        report_lines.append(
            "Duplicate edition in Olympic_Games_Summary.csv; "
            f"using first occurrence: {edition}"
        )

    return (
        games_df[["edition", "country_noc", "city"]]
        .drop_duplicates(subset=["edition"], keep="first")
        .rename(
            columns={
                "country_noc": HOST_COUNTRY_COLUMN,
                "city": HOST_CITY_COLUMN,
            }
        )
    )


def prepare_country_file(
    country_file: Path, report_lines: list[str]
) -> CountryIndicators:
    """Read and normalize one country CSV for repeated aggregation."""
    noc = country_file.stem

    try:
        country_df = pd.read_csv(country_file)
    except Exception as exc:  # noqa: BLE001 - keep the whole run alive.
        report_lines.append(f"Unable to read country file {country_file}: {exc}")
        return CountryIndicators(
            noc=noc,
            path=country_file,
            frame=pd.DataFrame(),
            indicator_columns=[],
            available_years=set(),
        )

    if "Year" not in country_df.columns:
        report_lines.append(f"Missing Year column in country file: {country_file}")
        return CountryIndicators(
            noc=noc,
            path=country_file,
            frame=pd.DataFrame(),
            indicator_columns=[],
            available_years=set(),
        )

    prepared_df = country_df.copy()
    indicator_columns = [column for column in prepared_df.columns if column != "Year"]

    year_text = prepared_df["Year"].astype(str).str.extract(r"^YR(\d+)$", expand=False)
    prepared_df[YEAR_NUMBER_COLUMN] = pd.to_numeric(year_text, errors="coerce")

    for column in indicator_columns:
        prepared_df[column] = pd.to_numeric(prepared_df[column], errors="coerce")

    available_years = set(
        prepared_df[YEAR_NUMBER_COLUMN].dropna().astype(int).tolist()
    )

    return CountryIndicators(
        noc=noc,
        path=country_file,
        frame=prepared_df,
        indicator_columns=indicator_columns,
        available_years=available_years,
    )


def load_country_indicator_files(
    clean_dir: Path, report_lines: list[str]
) -> tuple[dict[str, CountryIndicators], list[str]]:
    """Load every country CSV once and collect the complete indicator schema."""
    if not clean_dir.exists():
        report_lines.append(f"Clean directory not found: {clean_dir}")
        return {}, []

    countries: dict[str, CountryIndicators] = {}
    all_indicator_columns: list[str] = []

    for country_file in sorted(clean_dir.glob("*.csv")):
        country_data = prepare_country_file(country_file, report_lines)
        countries[country_data.noc] = country_data

        for column in country_data.indicator_columns:
            if column not in all_indicator_columns:
                all_indicator_columns.append(column)

    return countries, all_indicator_columns


def first_non_missing_value(values: pd.Series) -> object:
    """Return the first non-empty value from a Series, or pd.NA."""
    non_missing = values.dropna()
    if non_missing.empty:
        return pd.NA

    return non_missing.iloc[0]


def unique_value_for_year(frame: pd.DataFrame, year: object, column: str) -> object:
    """Copy a value only when it is unambiguous for the given Olympic year."""
    values = frame.loc[frame["year"] == year, column].dropna().unique()
    if len(values) == 1:
        return values[0]

    return pd.NA


def build_extra_row_template(
    main_df: pd.DataFrame, year: object, report_lines: list[str]
) -> dict[str, object]:
    """Create the base values for synthetic rows for a single Olympic year."""
    same_year = main_df.loc[main_df["year"] == year]
    template = {column: pd.NA for column in main_df.columns}

    template["year"] = year

    editions = same_year["edition"].dropna().unique()
    if len(editions) == 1:
        template["edition"] = editions[0]
    elif len(editions) > 1:
        # The specification treats year as the edition key. If the source data
        # has more than one edition in the same year, keep one deterministic
        # edition and record the ambiguity in the report.
        template["edition"] = first_non_missing_value(same_year["edition"])
        edition_text = ", ".join(str(edition) for edition in editions)
        report_lines.append(
            f"Multiple editions found for year {year}; "
            f"using {template['edition']} for added countries. Editions: {edition_text}"
        )

    for column in main_df.columns:
        if column in EXTRA_ROW_FIXED_COLUMNS:
            continue

        template[column] = unique_value_for_year(main_df, year, column)

    for medal_column in MEDAL_COLUMNS:
        template[medal_column] = 0

    return template


def add_missing_country_rows(
    main_df: pd.DataFrame,
    clean_country_codes: set[str],
    report_lines: list[str],
) -> pd.DataFrame:
    """Add countries from data/clean that are absent for a specific year."""
    extra_rows: list[dict[str, object]] = []

    for year in sorted(main_df["year"].dropna().unique()):
        same_year = main_df.loc[main_df["year"] == year]
        present_countries = {
            noc
            for noc in (normalize_noc(value) for value in same_year["country_noc"])
            if noc is not None
        }

        missing_countries = sorted(clean_country_codes.difference(present_countries))
        if not missing_countries:
            continue

        template = build_extra_row_template(main_df, year, report_lines)

        for country_noc in missing_countries:
            row = template.copy()
            row["country_noc"] = country_noc
            extra_rows.append(row)

    if not extra_rows:
        return main_df.copy()

    extra_df = pd.DataFrame(extra_rows, columns=main_df.columns)
    return pd.concat([main_df.copy(), extra_df], ignore_index=True)


def enrich_with_games_summary(
    base_df: pd.DataFrame,
    games_summary_df: pd.DataFrame,
    report_lines: list[str],
) -> pd.DataFrame:
    """Attach host country and city using edition, without overwriting country_noc."""
    enriched_df = base_df.merge(games_summary_df, on="edition", how="left")

    missing_mask = (
        enriched_df["edition"].notna()
        & enriched_df[HOST_COUNTRY_COLUMN].isna()
        & enriched_df[HOST_CITY_COLUMN].isna()
    )
    missing_editions = (
        enriched_df.loc[missing_mask, "edition"].dropna().astype(str).unique()
    )

    for edition in sorted(missing_editions):
        report_lines.append(
            f"Edition not found in Olympic_Games_Summary.csv: {edition}"
        )

    return enriched_df


def aggregate_country_indicators(
    country_data: CountryIndicators,
    olympic_year: int,
    years_to_aggregate: int,
) -> tuple[dict[str, object], list[int]]:
    """Average each numeric indicator over the available pre-Olympic years."""
    years = expected_previous_years(olympic_year, years_to_aggregate)
    missing_years = [
        year for year in years if year not in country_data.available_years
    ]

    if country_data.frame.empty or not country_data.indicator_columns:
        return {}, missing_years

    window_df = country_data.frame.loc[
        country_data.frame[YEAR_NUMBER_COLUMN].isin(years)
    ]
    averages = window_df[country_data.indicator_columns].mean(skipna=True).to_dict()

    return averages, missing_years


def build_indicator_columns(
    base_df: pd.DataFrame,
    country_data_by_noc: dict[str, CountryIndicators],
    all_indicator_columns: list[str],
    years_to_aggregate: int,
    report_lines: list[str],
) -> pd.DataFrame:
    """Calculate aggregated indicator values for every final medal row."""
    aggregated_rows: list[dict[str, object]] = []
    reported_missing_countries: set[str] = set()
    reported_missing_years: set[tuple[str, int, tuple[int, ...]]] = set()
    reported_invalid_year_rows: set[int] = set()

    for row_index, row in base_df.iterrows():
        aggregated_values = {column: pd.NA for column in all_indicator_columns}

        country_noc = normalize_noc(row["country_noc"])
        olympic_year = parse_year(row["year"])

        if country_noc is None:
            aggregated_rows.append(aggregated_values)
            continue

        country_data = country_data_by_noc.get(country_noc)
        if country_data is None:
            if country_noc not in reported_missing_countries:
                report_lines.append(f"Missing country indicator file: {country_noc}")
                reported_missing_countries.add(country_noc)

            aggregated_rows.append(aggregated_values)
            continue

        if olympic_year is None:
            if row_index not in reported_invalid_year_rows:
                report_lines.append(
                    f"Invalid Olympic year for country {country_noc} at row {row_index}"
                )
                reported_invalid_year_rows.add(row_index)

            aggregated_rows.append(aggregated_values)
            continue

        country_averages, missing_years = aggregate_country_indicators(
            country_data=country_data,
            olympic_year=olympic_year,
            years_to_aggregate=years_to_aggregate,
        )
        aggregated_values.update(country_averages)
        aggregated_rows.append(aggregated_values)

        if missing_years:
            key = (country_noc, olympic_year, tuple(missing_years))
            if key not in reported_missing_years:
                missing_text = ", ".join(str(year) for year in missing_years)
                report_lines.append(
                    f"Missing indicator years for {country_noc}, "
                    f"Olympic year {olympic_year}: {missing_text}"
                )
                reported_missing_years.add(key)

    return pd.DataFrame(aggregated_rows, columns=all_indicator_columns)


def write_outputs(
    final_df: pd.DataFrame, report_lines: list[str], output_dir: Path
) -> tuple[Path, Path]:
    """Write the final CSV and a readable missing-data report."""
    output_dir.mkdir(parents=True, exist_ok=True)

    output_csv = output_dir / OUTPUT_CSV_NAME
    report_file = output_dir / REPORT_NAME

    final_df.to_csv(output_csv, index=False)

    if report_lines:
        report_text = "\n".join(report_lines)
    else:
        report_text = "No missing data found."

    report_file.write_text(report_text + "\n", encoding="utf-8")
    return output_csv, report_file


def build_final_dataset(
    main_file: Path,
    games_summary_file: Path,
    clean_dir: Path,
    years_to_aggregate: int,
) -> tuple[pd.DataFrame, list[str]]:
    """Run the full enrichment workflow and return data plus report lines."""
    report_lines: list[str] = []

    main_df = load_main_data(main_file)
    games_summary_df = load_games_summary(games_summary_file, report_lines)
    country_data_by_noc, all_indicator_columns = load_country_indicator_files(
        clean_dir=clean_dir,
        report_lines=report_lines,
    )

    base_df = add_missing_country_rows(
        main_df=main_df,
        clean_country_codes=set(country_data_by_noc),
        report_lines=report_lines,
    )
    enriched_df = enrich_with_games_summary(
        base_df=base_df,
        games_summary_df=games_summary_df,
        report_lines=report_lines,
    )
    indicator_df = build_indicator_columns(
        base_df=enriched_df,
        country_data_by_noc=country_data_by_noc,
        all_indicator_columns=all_indicator_columns,
        years_to_aggregate=years_to_aggregate,
        report_lines=report_lines,
    )

    final_columns = (
        list(main_df.columns)
        + [HOST_COUNTRY_COLUMN, HOST_CITY_COLUMN]
        + all_indicator_columns
    )
    final_df = pd.concat(
        [
            enriched_df[list(main_df.columns) + [HOST_COUNTRY_COLUMN, HOST_CITY_COLUMN]]
            .reset_index(drop=True),
            indicator_df.reset_index(drop=True),
        ],
        axis=1,
    )

    return final_df[final_columns], report_lines


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse configurable input, output, and aggregation settings."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate an Olympic medal CSV enriched with socioeconomic indicators."
        )
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Directory containing the main Olympic CSV files.",
    )
    parser.add_argument(
        "--main-file",
        type=Path,
        default=None,
        help="Path to Olympic_Medal_Tally_History_definitivo.csv.",
    )
    parser.add_argument(
        "--games-summary-file",
        type=Path,
        default=None,
        help="Path to Olympic_Games_Summary.csv.",
    )
    parser.add_argument(
        "--clean-dir",
        type=Path,
        default=None,
        help="Directory containing country socioeconomic CSV files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where the final CSV and report will be written.",
    )
    parser.add_argument(
        "--years-to-aggregate",
        type=int,
        default=DEFAULT_YEARS_TO_AGGREGATE,
        help="Number of years before each Olympics to average.",
    )
    return parser.parse_args(argv)


def resolve_paths(args: argparse.Namespace) -> tuple[Path, Path, Path, Path]:
    """Resolve default paths from data-dir unless explicit paths are provided."""
    data_dir = args.data_dir
    main_file = args.main_file or data_dir / DEFAULT_MAIN_FILENAME
    games_summary_file = (
        args.games_summary_file or data_dir / DEFAULT_GAMES_SUMMARY_FILENAME
    )
    clean_dir = args.clean_dir or data_dir / DEFAULT_CLEAN_DIRNAME

    return main_file, games_summary_file, clean_dir, args.output_dir


def main(argv: Optional[Sequence[str]] = None) -> None:
    """Create the enriched Olympic medal CSV and the missing-data report."""
    args = parse_args(argv)
    main_file, games_summary_file, clean_dir, output_dir = resolve_paths(args)

    final_df, report_lines = build_final_dataset(
        main_file=main_file,
        games_summary_file=games_summary_file,
        clean_dir=clean_dir,
        years_to_aggregate=args.years_to_aggregate,
    )
    output_csv, report_file = write_outputs(
        final_df=final_df,
        report_lines=report_lines,
        output_dir=output_dir,
    )

    print(f"CSV written to: {output_csv}")
    print(f"Missing-data report written to: {report_file}")


if __name__ == "__main__":
    main()
