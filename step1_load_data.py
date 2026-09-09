import csv
import sqlite3
from pathlib import Path


# File directory
ROOT_DIR = Path(__file__).resolve().parent

CSV_PATH = ROOT_DIR / "cell-count.csv"
DB_PATH = ROOT_DIR / "cell_counts.db"

CELL_POPULATIONS = [
    "b_cell",
    "cd8_t_cell",
    "cd4_t_cell",
    "nk_cell",
    "monocyte",
]



CREATE_TABLES_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS samples (
    sample TEXT PRIMARY KEY,
    project TEXT NOT NULL,
    subject TEXT NOT NULL,
    condition TEXT,
    age REAL,
    sex TEXT,
    treatment TEXT,
    response TEXT,
    sample_type TEXT,
    time_from_treatment_start REAL
);

CREATE TABLE IF NOT EXISTS populations (
    population_id INTEGER PRIMARY KEY AUTOINCREMENT,
    population_name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS cell_counts (
    sample TEXT NOT NULL,
    population_id INTEGER NOT NULL,
    count INTEGER NOT NULL CHECK (count >= 0),

    PRIMARY KEY (sample, population_id),

    FOREIGN KEY (sample)
        REFERENCES samples(sample)
        ON DELETE CASCADE,

    FOREIGN KEY (population_id)
        REFERENCES populations(population_id)
);
"""


# Database setup

def create_database(connection):
    """Create the tables"""
    connection.executescript(CREATE_TABLES_SQL)


def insert_populations(connection):
    """Insert immune cell populations."""

    connection.executemany(
        """
        INSERT OR IGNORE INTO populations (population_name)
        VALUES (?);
        """,
        [(population,) for population in CELL_POPULATIONS],
    )


# Load CSV data

def load_csv(connection):
    """Read cell-count.csv and insert all rows into SQLite"""

    with open(CSV_PATH, "r", newline="", encoding="utf-8-sig") as csv_file:

        reader = csv.DictReader(csv_file)

        print("CSV columns:")
        print(reader.fieldnames)

        population_ids = {
            population_name: population_id
            for population_id, population_name in connection.execute(
                """
                SELECT population_id, population_name
                FROM populations;
                """
            )
        }

        for row in reader:
            # inserting sample metadata

            connection.execute(
                """
                INSERT INTO samples (
                    sample,
                    project,
                    subject,
                    condition,
                    age,
                    sex,
                    treatment,
                    response,
                    sample_type,
                    time_from_treatment_start
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    row["sample"],
                    row["project"],
                    row["subject"],
                    row["condition"],
                    float(row["age"]) if row["age"] else None,
                    row["sex"],
                    row["treatment"],
                    row["response"],
                    row["sample_type"],
                    (
                        float(row["time_from_treatment_start"])
                        if row["time_from_treatment_start"]
                        else None
                    ),
                ),
            )

            # convert five population columns into rows

            for population_name in CELL_POPULATIONS:
                count = row[population_name]
                if count == "":
                    count = 0
                else:
                    count = int(float(count))

                connection.execute(
                    """
                    INSERT INTO cell_counts (
                        sample,
                        population_id,
                        count
                    )
                    VALUES (?, ?, ?);
                    """,
                    (
                        row["sample"],
                        population_ids[population_name],
                        count,
                    ),
                )


# Main 

def main():

    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Could not find {CSV_PATH.name}. "
            "Make sure cell-count.csv is in the repository root."
        )

    if DB_PATH.exists():
        DB_PATH.unlink()

    connection = sqlite3.connect(DB_PATH)

    connection.execute("PRAGMA foreign_keys = ON;")

    try:
        create_database(connection)
        insert_populations(connection)
        load_csv(connection)

        connection.commit()

        # validation 
        sample_count = connection.execute(
            "SELECT COUNT(*) FROM samples;"
        ).fetchone()[0]

        cell_count_rows = connection.execute(
            "SELECT COUNT(*) FROM cell_counts;"
        ).fetchone()[0]

        population_count = connection.execute(
            "SELECT COUNT(*) FROM populations;"
        ).fetchone()[0]

        print()
        print("Database loaded successfully.")
        print(f"Samples: {sample_count}")
        print(f"Populations: {population_count}")
        print(f"Cell-count records: {cell_count_rows}")
        print(f"Database: {DB_PATH}")

    finally:
        connection.close()


if __name__ == "__main__":
    main()

