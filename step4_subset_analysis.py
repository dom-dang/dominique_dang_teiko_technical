import sqlite3
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parent
DB_PATH = ROOT_DIR / "cell_counts.db"

BASELINE_OUTPUT_PATH = ROOT_DIR / "miraclib_melanoma_pbmc_baseline.csv"
PROJECT_OUTPUT_PATH = ROOT_DIR / "baseline_samples_by_project.csv"
RESPONSE_OUTPUT_PATH = ROOT_DIR / "baseline_subjects_by_response.csv"
SEX_OUTPUT_PATH = ROOT_DIR / "baseline_subjects_by_sex.csv"


def get_baseline_samples(connection):
    """
    Return melanoma PBMC baseline samples from subjects treated
    with miraclib.
    """

    query = """
    SELECT
        sample,
        subject,
        project,
        condition,
        treatment,
        response,
        sex,
        sample_type,
        time_from_treatment_start
    FROM samples
    WHERE LOWER(condition) = 'melanoma'
      AND LOWER(treatment) = 'miraclib'
      AND LOWER(sample_type) = 'pbmc'
      AND time_from_treatment_start = 0
    ORDER BY project, subject, sample;
    """

    return pd.read_sql_query(query, connection)


def summarize_by_project(baseline):
    """
    Count baseline samples in each project.
    """

    return (
        baseline
        .groupby("project")
        .size()
        .reset_index(name="sample_count")
        .sort_values("project")
    )


def summarize_by_response(baseline):
    """
    Count unique subjects by responder/non-responder status.
    """

    unique_subjects = baseline[
        ["subject", "response"]
    ].drop_duplicates()

    return (
        unique_subjects
        .groupby("response")
        .size()
        .reset_index(name="subject_count")
    )


def summarize_by_sex(baseline):
    """
    Count unique subjects by sex.
    """

    unique_subjects = baseline[
        ["subject", "sex"]
    ].drop_duplicates()

    return (
        unique_subjects
        .groupby("sex")
        .size()
        .reset_index(name="subject_count")
    )

def get_average_b_cells_melanoma_male_responders_baseline(connection):
    """ 
    For the Google Form Question 
    """
    query = """
    SELECT AVG(c.count) AS average_b_cells
    FROM samples AS s
    JOIN cell_counts AS c
        ON s.sample = c.sample
    JOIN populations AS p
        ON c.population_id = p.population_id
    WHERE LOWER(s.condition) = 'melanoma'
      AND LOWER(s.sex) IN ('m', 'male')
      AND LOWER(s.response) = 'yes'
      AND s.time_from_treatment_start = 0
      AND p.population_name = 'b_cell';
    """
    return connection.execute(query).fetchone()[0]


def main():
    connection = sqlite3.connect(DB_PATH)

    try:
        baseline = get_baseline_samples(connection)

        project_summary = summarize_by_project(baseline)
        response_summary = summarize_by_response(baseline)
        sex_summary = summarize_by_sex(baseline)

        baseline.to_csv(BASELINE_OUTPUT_PATH, index=False)
        project_summary.to_csv(PROJECT_OUTPUT_PATH, index=False)
        response_summary.to_csv(RESPONSE_OUTPUT_PATH, index=False)
        sex_summary.to_csv(SEX_OUTPUT_PATH, index=False)

        print("Baseline melanoma PBMC miraclib samples:")
        print(baseline.head(10))

        print()
        print(f"Total baseline samples: {len(baseline)}")
        print(f"Unique subjects: {baseline['subject'].nunique()}")

        print()
        print("Samples by project:")
        print(project_summary)

        print()
        print("Subjects by response:")
        print(response_summary)

        print()
        print("Subjects by sex:")
        print(sex_summary)

    finally:
        connection.close()


if __name__ == "__main__":
    main()