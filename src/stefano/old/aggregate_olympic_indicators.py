import argparse
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_MAIN_FILE = PROJECT_ROOT / "data" / "Olympic_Medal_Tally_History_definitivo.csv"
DEFAULT_CLEAN_DIR = PROJECT_ROOT / "clean"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"
DEFAULT_YEARS_TO_AGGREGATE = 4

OUTPUT_CSV_NAME = "olympic_medals_with_socioeconomic_indicators.csv"
REPORT_NAME = "missing_data_report.txt"


CountryData = Tuple[pd.DataFrame, List[str]]


def resolve_clean_dir(clean_dir: Path) -> Path:
    """Return the requested clean directory, with a project-specific fallback."""
    if clean_dir.exists():
        return clean_dir

    fallback_dir = PROJECT_ROOT / "data" / "clean"
    if clean_dir == DEFAULT_CLEAN_DIR and fallback_dir.exists():
        return fallback_dir

    return clean_dir


def load_main_data(main_file: Path) -> pd.DataFrame:
    """Load the Olympic medal tally file without changing original columns."""
    olympic_df = pd.read_csv(main_file)
    required_columns = {"year", "country_noc"}
    missing_columns = required_columns.difference(olympic_df.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns in main file: {missing}")

    return olympic_df


def load_country_data(country_noc: str, clean_dir: Path) -> Optional[CountryData]:
    """Load and prepare one country CSV, returning None if it does not exist."""
    country_file = clean_dir / f"{country_noc}.csv"
    if not country_file.exists():
        return None

    country_df = pd.read_csv(country_file)
    if "Year" not in country_df.columns:
        raise ValueError(f"Missing required column 'Year' in {country_file}")

    prepared_df = country_df.copy()
    indicator_columns = [column for column in prepared_df.columns if column != "Year"]

    prepared_df["year_number"] = (
        prepared_df["Year"].astype(str).str.replace("YR", "", regex=False)
    )
    prepared_df["year_number"] = pd.to_numeric(
        prepared_df["year_number"], errors="coerce"
    )

    for column in indicator_columns:
        prepared_df[column] = pd.to_numeric(prepared_df[column], errors="coerce")

    return prepared_df, indicator_columns


def expected_previous_years(olympic_year: int, years_to_aggregate: int) -> List[int]:
    """Return the years used for the rolling pre-Olympic average."""
    return list(range(olympic_year - years_to_aggregate, olympic_year))


def aggregate_indicators(
    country_df: pd.DataFrame,
    indicator_columns: List[str],
    olympic_year: int,
    years_to_aggregate: int,
) -> Tuple[Dict[str, float], List[int]]:
    """Average available indicators over the years before an Olympic edition."""
    years = expected_previous_years(olympic_year, years_to_aggregate)
    available_years = set(country_df["year_number"].dropna().astype(int))
    missing_years = [year for year in years if year not in available_years]

    window_df = country_df[country_df["year_number"].isin(years)]
    aggregated_values = window_df[indicator_columns].mean(skipna=True).to_dict()

    return aggregated_values, missing_years


def build_aggregated_dataset(
    olympic_df: pd.DataFrame,
    clean_dir: Path,
    years_to_aggregate: int = DEFAULT_YEARS_TO_AGGREGATE,
) -> Tuple[pd.DataFrame, List[str]]:
    """Append aggregated socioeconomic indicators to every Olympic medal row."""
    country_cache: Dict[str, Optional[CountryData]] = {}
    missing_countries: Set[str] = set()
    report_lines: List[str] = []
    aggregated_rows: List[Dict[str, float]] = []
    all_indicator_columns: List[str] = []

    for _, row in olympic_df.iterrows():
        country_noc = str(row["country_noc"])
        olympic_year = int(row["year"])

        if country_noc not in country_cache:
            country_cache[country_noc] = load_country_data(country_noc, clean_dir)

        country_data = country_cache[country_noc]
        if country_data is None:
            missing_countries.add(country_noc)
            aggregated_rows.append({})
            continue

        country_df, indicator_columns = country_data
        for column in indicator_columns:
            if column not in all_indicator_columns:
                all_indicator_columns.append(column)

        aggregated_values, missing_years = aggregate_indicators(
            country_df=country_df,
            indicator_columns=indicator_columns,
            olympic_year=olympic_year,
            years_to_aggregate=years_to_aggregate,
        )
        aggregated_rows.append(aggregated_values)

        if missing_years:
            missing = ", ".join(str(year) for year in missing_years)
            report_lines.append(
                f"{country_noc} - Olympic year {olympic_year}: missing years {missing}"
            )

    indicator_df = pd.DataFrame(aggregated_rows, columns=all_indicator_columns)
    final_df = pd.concat(
        [olympic_df.reset_index(drop=True), indicator_df.reset_index(drop=True)],
        axis=1,
    )

    country_report_lines = [
        f"{country_noc}: missing country file" for country_noc in sorted(missing_countries)
    ]

    return final_df, country_report_lines + report_lines


def write_outputs(
    final_df: pd.DataFrame,
    report_lines: List[str],
    output_dir: Path,
) -> Tuple[Path, Path]:
    """Write the aggregated CSV and the missing-data report."""
    output_dir.mkdir(parents=True, exist_ok=True)

    output_csv = output_dir / OUTPUT_CSV_NAME
    report_file = output_dir / REPORT_NAME

    final_df.to_csv(output_csv, index=False)

    if report_lines:
        report_text = "\n".join(report_lines)
    else:
        report_text = "No missing country files or missing years found."

    report_file.write_text(report_text + "\n", encoding="utf-8")
    return output_csv, report_file


def parse_args() -> argparse.Namespace:
    """Parse optional paths and aggregation settings from the command line."""
    parser = argparse.ArgumentParser(
        description=(
            "Aggregate socioeconomic indicators into the Olympic medal tally dataset."
        )
    )
    parser.add_argument(
        "--main-file",
        type=Path,
        default=DEFAULT_MAIN_FILE,
        help="Path to Olympic_Medal_Tally_History_definitivo.csv.",
    )
    parser.add_argument(
        "--clean-dir",
        type=Path,
        default=DEFAULT_CLEAN_DIR,
        help="Directory containing country indicator CSV files.",
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
        help="Number of previous years to use for each indicator average.",
    )
    return parser.parse_args()


def main(
    main_file: Path,
    clean_dir: Path,
    output_dir: Path,
    years_to_aggregate: int,
) -> None:
    """Generate the Olympic medal dataset enriched with socioeconomic indicators."""
    clean_dir = resolve_clean_dir(clean_dir)

    olympic_df = load_main_data(main_file)
    final_df, report_lines = build_aggregated_dataset(
        olympic_df=olympic_df,
        clean_dir=clean_dir,
        years_to_aggregate=years_to_aggregate,
    )
    output_csv, report_file = write_outputs(
        final_df=final_df,
        report_lines=report_lines,
        output_dir=output_dir,
    )

    print(f"CSV written to: {output_csv}")
    print(f"Missing-data report written to: {report_file}")


if __name__ == "__main__":
    args = parse_args()
    main(
        main_file=args.main_file,
        clean_dir=args.clean_dir,
        output_dir=args.output_dir,
        years_to_aggregate=args.years_to_aggregate,
    )
