import sqlite3
from pathlib import Path
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parent
DB_PATH = ROOT_DIR / "cell_counts.db"
OUTPUT_PATH = ROOT_DIR / "cell_frequency_summary.csv"


def get_cell_frequency_summary(connection):
    """
    Return a table with one row per sample/population containing:
    sample, total_count, population, count, percentage.
    """

    query = """
    SELECT
        c.sample,
        SUM(c.count) OVER (PARTITION BY c.sample) AS total_count,
        p.population_name AS population,
        c.count,
        100.0 * c.count
            / SUM(c.count) OVER (PARTITION BY c.sample) AS percentage
    FROM cell_counts AS c
    JOIN populations AS p
        ON c.population_id = p.population_id
    ORDER BY c.sample, p.population_name;
    """

    return pd.read_sql_query(query, connection)


def main():
    connection = sqlite3.connect(DB_PATH)

    summary = get_cell_frequency_summary(connection)

    percentage_check = (
        summary.groupby("sample")["percentage"]
        .sum()
        .round(6)
    )

    invalid_samples = percentage_check[
        (percentage_check < 99.999) | (percentage_check > 100.001)
    ]

    if len(invalid_samples) > 0:
        print("Warning: some samples do not sum to 100%:")
        print(invalid_samples.head())
    else:
        print("Validation passed: all sample percentages sum to 100%.")

    summary.to_csv(OUTPUT_PATH, index=False)

    print(summary.head(10))
    print()
    print(f"Summary rows: {len(summary)}")
    print(f"Saved summary table to: {OUTPUT_PATH}")

    connection.close()

if __name__ == "__main__":
    main()