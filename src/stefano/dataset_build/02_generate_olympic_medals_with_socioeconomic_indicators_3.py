import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_MAIN_FILE = DEFAULT_DATA_DIR / "csv_olimpiadi" / "Olympic_Medal_Tally_History_definitivo.csv"
DEFAULT_SUMMARY_FILE = DEFAULT_DATA_DIR / "csv_olimpiadi" / "Olympic_Games_Summary.csv"
DEFAULT_CLEAN_DIR = DEFAULT_DATA_DIR / "csv_wb_paesi"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "test2"
DEFAULT_YEARS_TO_AGGREGATE = 4

OUTPUT_CSV_NAME = "olympic_medals_with_socioeconomic_indicators_3.csv"
REPORT_NAME = "missing_data_report_3.txt"

REQUIRED_MAIN_COLUMNS = {
    "edition",
    "year",
    "country_noc",
    "gold",
    "silver",
    "bronze",
    "total",
}
REQUIRED_SUMMARY_COLUMNS = {"edition", "year", "country_noc", "city"}
FIXED_NEW_ROW_COLUMNS = {
    "edition",
    "year",
    "country_noc",
    "gold",
    "silver",
    "bronze",
    "total",
}
MEDAL_COLUMNS = ["gold", "silver", "bronze", "total"]
OLYMPIC_PLACE_COLUMNS = ["paese_olimpiade", "citta_olimpiade"]


@dataclass
class CountryIndicators:
    """Prepared socioeconomic indicators for one country."""

    dataframe: pd.DataFrame
    indicator_columns: list[str]


@dataclass
class AggregationContext:
    """Reusable data needed while building original and extra Olympic rows."""

    country_data: dict[str, CountryIndicators]
    all_indicator_columns: list[str]
    summary_lookup: dict[tuple[int, str], dict[str, Any]]
    years_to_aggregate: int
    missing_country_files: set[str]
    missing_year_entries: set[tuple[str, int, str, tuple[int, ...]]]


def normalize_country_noc(value: Any) -> str:
    """Return a country NOC code suitable for matching file names."""
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_edition(value: Any) -> str:
    """Return the Olympic edition value used in the composite key."""
    if pd.isna(value):
        return ""
    return str(value).strip()


def parse_year(value: Any) -> int:
    """Parse a year value without mutating the source dataframe."""
    parsed = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(parsed):
        raise ValueError(f"Invalid Olympic year: {value!r}")
    return int(parsed)


def olympic_key(year: Any, edition: Any) -> tuple[int, str]:
    """Build the unique Olympic Games key from year and edition."""
    return parse_year(year), normalize_edition(edition)


def validate_columns(
    dataframe: pd.DataFrame,
    required_columns: set[str],
    source_path: Path,
) -> None:
    """Raise a clear error if an input CSV is missing required columns."""
    missing_columns = required_columns.difference(dataframe.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns in {source_path}: {missing}")


def read_main_file(main_file: Path) -> pd.DataFrame:
    """Load the main Olympic medal tally, preserving its original columns."""
    main_df = pd.read_csv(main_file)
    validate_columns(main_df, REQUIRED_MAIN_COLUMNS, main_file)
    return main_df


def read_games_summary(
    summary_file: Path,
    report_lines: list[str],
) -> dict[tuple[int, str], dict[str, Any]]:
    """Load host country and city for each Olympic edition."""
    summary_df = pd.read_csv(summary_file)
    validate_columns(summary_df, REQUIRED_SUMMARY_COLUMNS, summary_file)

    lookup: dict[tuple[int, str], dict[str, Any]] = {}
    duplicate_keys: set[tuple[int, str]] = set()

    for _, row in summary_df.iterrows():
        key = olympic_key(row["year"], row["edition"])
        value = {
            "paese_olimpiade": row["country_noc"],
            "citta_olimpiade": row["city"],
        }

        if key in lookup and lookup[key] != value:
            duplicate_keys.add(key)
            continue

        lookup[key] = value

    for year, edition in sorted(duplicate_keys):
        report_lines.append(
            "Duplicate Olympic summary rows with conflicting host data ignored "
            f"for year={year}, edition={edition}"
        )

    return lookup


def read_country_file(country_file: Path) -> CountryIndicators | None:
    """Load one country indicator file and convert indicator values to numeric."""
    country_df = pd.read_csv(country_file)
    if "Year" not in country_df.columns:
        return None

    prepared_df = country_df.copy()
    indicator_columns = [column for column in prepared_df.columns if column != "Year"]

    prepared_df["_year_number"] = pd.to_numeric(
        prepared_df["Year"].astype(str).str.replace("YR", "", regex=False),
        errors="coerce",
    )

    for column in indicator_columns:
        prepared_df[column] = pd.to_numeric(prepared_df[column], errors="coerce")

    return CountryIndicators(
        dataframe=prepared_df,
        indicator_columns=indicator_columns,
    )


def read_all_country_files(
    clean_dir: Path,
    report_lines: list[str],
) -> tuple[dict[str, CountryIndicators], list[str]]:
    """Load each country CSV once and collect the complete indicator schema."""
    country_data: dict[str, CountryIndicators] = {}
    all_indicator_columns: list[str] = []

    for country_file in sorted(clean_dir.glob("*.csv")):
        country_noc = country_file.stem
        indicators = read_country_file(country_file)

        if indicators is None:
            report_lines.append(
                f"{country_noc}: missing required Year column in {country_file}"
            )
            continue

        country_data[country_noc] = indicators
        for column in indicators.indicator_columns:
            if column not in all_indicator_columns:
                all_indicator_columns.append(column)

    return country_data, all_indicator_columns


def previous_years(olympic_year: int, years_to_aggregate: int) -> list[int]:
    """Return the years used for pre-Olympic aggregation."""
    return list(range(olympic_year - years_to_aggregate, olympic_year))


def empty_indicator_values(indicator_columns: list[str]) -> dict[str, Any]:
    """Return NaN values for all socioeconomic indicator columns."""
    return {column: pd.NA for column in indicator_columns}


def aggregate_country_indicators(
    country_noc: str,
    olympic_year: int,
    edition: str,
    context: AggregationContext,
) -> dict[str, Any]:
    """Average available country indicators over the previous Olympic years."""
    if country_noc not in context.country_data:
        context.missing_country_files.add(country_noc)
        return empty_indicator_values(context.all_indicator_columns)

    indicators = context.country_data[country_noc]
    target_years = previous_years(olympic_year, context.years_to_aggregate)
    available_years = set(
        indicators.dataframe["_year_number"].dropna().astype(int).tolist()
    )
    missing_years = tuple(year for year in target_years if year not in available_years)

    if missing_years:
        context.missing_year_entries.add(
            (country_noc, olympic_year, edition, missing_years)
        )

    window_df = indicators.dataframe[
        indicators.dataframe["_year_number"].isin(target_years)
    ]
    aggregated_values = empty_indicator_values(context.all_indicator_columns)

    if not window_df.empty and indicators.indicator_columns:
        means = window_df[indicators.indicator_columns].mean(skipna=True)
        for column, value in means.items():
            aggregated_values[column] = value

    return aggregated_values


def get_olympic_place(
    key: tuple[int, str],
    summary_lookup: dict[tuple[int, str], dict[str, Any]],
) -> dict[str, Any]:
    """Return host country and city, or NaN values if the edition is missing."""
    default_place = {"paese_olimpiade": pd.NA, "citta_olimpiade": pd.NA}
    return summary_lookup.get(key, default_place).copy()


def find_missing_summary_pairs(
    main_df: pd.DataFrame,
    summary_lookup: dict[tuple[int, str], dict[str, Any]],
) -> list[tuple[int, str]]:
    """Find Olympic editions from the main file missing in the summary file."""
    missing_pairs: set[tuple[int, str]] = set()

    for _, row in main_df[["year", "edition"]].drop_duplicates().iterrows():
        key = olympic_key(row["year"], row["edition"])
        if key not in summary_lookup:
            missing_pairs.add(key)

    return sorted(missing_pairs)


def get_pair_derived_columns(main_df: pd.DataFrame) -> set[str]:
    """Find original columns that are functionally determined by year+edition."""
    candidate_columns = [
        column
        for column in main_df.columns
        if column not in FIXED_NEW_ROW_COLUMNS
    ]
    pair_derived_columns: set[str] = set()

    for column in candidate_columns:
        unique_counts = main_df.groupby(["year", "edition"], dropna=False)[
            column
        ].nunique(dropna=True)

        if (unique_counts <= 1).all():
            pair_derived_columns.add(column)

    return pair_derived_columns


def get_unique_pair_values(
    group_df: pd.DataFrame,
    pair_derived_columns: set[str],
) -> dict[str, Any]:
    """Extract values that can be copied to added rows for one Olympic edition."""
    values: dict[str, Any] = {}

    for column in pair_derived_columns:
        non_null_values = group_df[column].dropna().unique()
        values[column] = non_null_values[0] if len(non_null_values) == 1 else pd.NA

    return values


def build_original_row(
    source_row: pd.Series,
    context: AggregationContext,
) -> dict[str, Any]:
    """Build one enriched row that already exists in the main dataset."""
    row_dict = source_row.to_dict()
    year, edition = olympic_key(source_row["year"], source_row["edition"])
    country_noc = normalize_country_noc(source_row["country_noc"])

    row_dict.update(get_olympic_place((year, edition), context.summary_lookup))
    row_dict.update(
        aggregate_country_indicators(
            country_noc=country_noc,
            olympic_year=year,
            edition=edition,
            context=context,
        )
    )

    return row_dict


def build_extra_row(
    country_noc: str,
    olympic_year: int,
    edition: str,
    source_year_value: Any,
    pair_values: dict[str, Any],
    original_columns: list[str],
    context: AggregationContext,
) -> dict[str, Any]:
    """Build one zero-medal row for a country absent from a specific edition."""
    row_dict = {column: pd.NA for column in original_columns}
    row_dict.update(pair_values)
    row_dict["year"] = source_year_value
    row_dict["edition"] = edition
    row_dict["country_noc"] = country_noc

    for column in MEDAL_COLUMNS:
        row_dict[column] = 0

    row_dict.update(get_olympic_place((olympic_year, edition), context.summary_lookup))
    row_dict.update(
        aggregate_country_indicators(
            country_noc=country_noc,
            olympic_year=olympic_year,
            edition=edition,
            context=context,
        )
    )

    return row_dict


def build_enriched_dataset(
    main_df: pd.DataFrame,
    context: AggregationContext,
) -> pd.DataFrame:
    """Create the final dataset with original and added country-edition rows."""
    output_rows: list[dict[str, Any]] = []

    for _, row in main_df.iterrows():
        output_rows.append(build_original_row(row, context))

    pair_derived_columns = get_pair_derived_columns(main_df)
    clean_countries = set(context.country_data.keys())

    for (year_value, edition_value), group_df in main_df.groupby(
        ["year", "edition"],
        sort=False,
        dropna=False,
    ):
        olympic_year, edition = olympic_key(year_value, edition_value)
        present_countries = {
            normalize_country_noc(country)
            for country in group_df["country_noc"].dropna().tolist()
        }
        pair_values = get_unique_pair_values(group_df, pair_derived_columns)

        for country_noc in sorted(clean_countries.difference(present_countries)):
            output_rows.append(
                build_extra_row(
                    country_noc=country_noc,
                    olympic_year=olympic_year,
                    edition=edition,
                    source_year_value=year_value,
                    pair_values=pair_values,
                    original_columns=list(main_df.columns),
                    context=context,
                )
            )

    output_columns = (
        list(main_df.columns)
        + OLYMPIC_PLACE_COLUMNS
        + context.all_indicator_columns
    )
    return pd.DataFrame(output_rows, columns=output_columns)


def build_report_lines(
    initial_report_lines: list[str],
    missing_summary_pairs: list[tuple[int, str]],
    missing_country_files: set[str],
    missing_year_entries: set[tuple[str, int, str, tuple[int, ...]]],
) -> list[str]:
    """Format all data-quality messages for the output report."""
    report_lines = list(initial_report_lines)

    for year, edition in missing_summary_pairs:
        report_lines.append(
            "Missing Olympic summary match for "
            f"year={year}, edition={edition}"
        )

    for country_noc in sorted(country for country in missing_country_files if country):
        report_lines.append(f"{country_noc}: missing country file in data/clean")

    for country_noc, olympic_year, edition, missing_years in sorted(
        missing_year_entries
    ):
        years = ", ".join(str(year) for year in missing_years)
        report_lines.append(
            f"{country_noc} - year={olympic_year}, edition={edition}: "
            f"missing previous years {years}"
        )

    if not report_lines:
        report_lines.append("No missing data found.")

    return report_lines


def write_outputs(
    final_df: pd.DataFrame,
    report_lines: list[str],
    output_dir: Path,
) -> tuple[Path, Path]:
    """Write the final CSV and missing-data report."""
    output_dir.mkdir(parents=True, exist_ok=True)

    output_csv = output_dir / OUTPUT_CSV_NAME
    report_file = output_dir / REPORT_NAME

    final_df.to_csv(output_csv, index=False)
    report_file.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    return output_csv, report_file


def parse_args() -> argparse.Namespace:
    """Parse paths and aggregation settings from the command line."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate an Olympic medal CSV enriched with socioeconomic indicators."
        )
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Directory containing Olympic_Games_Summary.csv and clean/.",
    )
    parser.add_argument(
        "--main-file",
        type=Path,
        default=None,
        help="Path to Olympic_Medal_Tally_History_definitivo.csv. Defaults to data-dir value.",
    )
    parser.add_argument(
        "--summary-file",
        type=Path,
        default=None,
        help="Path to Olympic_Games_Summary.csv. Defaults to data-dir value.",
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
        help="Directory where output files will be written.",
    )
    parser.add_argument(
        "--years-to-aggregate",
        type=int,
        default=DEFAULT_YEARS_TO_AGGREGATE,
        help="Number of previous years to average for each indicator.",
    )
    return parser.parse_args()


def main(
    main_file: Path = DEFAULT_MAIN_FILE,
    summary_file: Path = DEFAULT_SUMMARY_FILE,
    clean_dir: Path = DEFAULT_CLEAN_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    years_to_aggregate: int = DEFAULT_YEARS_TO_AGGREGATE,
) -> None:
    """Generate the enriched Olympic medal dataset and missing-data report."""
    report_lines: list[str] = []

    main_df = read_main_file(main_file)
    summary_lookup = read_games_summary(summary_file, report_lines)
    country_data, all_indicator_columns = read_all_country_files(
        clean_dir=clean_dir,
        report_lines=report_lines,
    )

    context = AggregationContext(
        country_data=country_data,
        all_indicator_columns=all_indicator_columns,
        summary_lookup=summary_lookup,
        years_to_aggregate=years_to_aggregate,
        missing_country_files=set(),
        missing_year_entries=set(),
    )

    missing_summary_pairs = find_missing_summary_pairs(main_df, summary_lookup)
    final_df = build_enriched_dataset(main_df, context)
    final_report_lines = build_report_lines(
        initial_report_lines=report_lines,
        missing_summary_pairs=missing_summary_pairs,
        missing_country_files=context.missing_country_files,
        missing_year_entries=context.missing_year_entries,
    )
    output_csv, report_file = write_outputs(
        final_df=final_df,
        report_lines=final_report_lines,
        output_dir=output_dir,
    )

    print(f"CSV written to: {output_csv}")
    print(f"Missing-data report written to: {report_file}")


if __name__ == "__main__":
    args = parse_args()
    resolved_main_file = (
        args.main_file
        if args.main_file is not None
        else DEFAULT_MAIN_FILE
    )
    resolved_summary_file = (
        args.summary_file
        if args.summary_file is not None
        else DEFAULT_SUMMARY_FILE
    )
    resolved_clean_dir = (
        args.clean_dir if args.clean_dir is not None else DEFAULT_CLEAN_DIR
    )

    main(
        main_file=resolved_main_file,
        summary_file=resolved_summary_file,
        clean_dir=resolved_clean_dir,
        output_dir=args.output_dir,
        years_to_aggregate=args.years_to_aggregate,
    )
