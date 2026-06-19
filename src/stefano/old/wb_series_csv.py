import pandas as pd
import wbgapi as wb


def normalize_time(time_input):
    if isinstance(time_input, int):
        return f"YR{time_input}"
    return time_input


def export_world_bank_data(indicators_dict, countries, time_input, output_csv="wb_data.csv"):
    all_rows = []

    for item in indicators_dict:
        dbid = item["dbid"]
        indicators = item["indicators"]

        series = list(indicators.keys())
        labels = list(indicators.values())

        df = wb.data.DataFrame(
            series=series,
            labels=labels,
            economy=countries,
            time=normalize_time(time_input),
            db=dbid
        )

        df = df.reset_index()

        # colonne anni
        year_columns = [c for c in df.columns if str(c).startswith("YR")]

        # tutte le altre
        id_columns = [c for c in df.columns if c not in year_columns]

        # trasformazione wide -> long
        df_long = df.melt(
            id_vars=id_columns,
            value_vars=year_columns,
            var_name="time",
            value_name="value"
        )
        
        # se esiste una colonna con label indicatore
        indicator_column = None

        for c in df_long.columns:
            if c not in ["economy", "time", "value"]:
                indicator_column = c
                break

        if indicator_column:
            df_long = df_long.rename(
                columns={indicator_column: "indicator_name"}
            )

        df_long["dbid"] = dbid
        all_rows.append(df_long)

    result = pd.concat(all_rows, ignore_index=True)
    result.to_csv(output_csv, index=False)
    return result



if __name__ == "__main__":

    indicators_dict = [{
        "dbid": 3,
        "indicators": {
            "GOV_WGI_PV.SC":"Political Stability - score (0-100)",
            "GOV_WGI_CC.SC":"Control of Corruption - score(0 - 100)"
        }
    }]

    countries = ["USA", "CAN", "MEX", "ITA"]

    time_range = range(2020, 2025)

    df = export_world_bank_data(
        indicators_dict,
        countries,
        time_range
    )

    print(df.head())