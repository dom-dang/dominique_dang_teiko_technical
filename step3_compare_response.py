import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy.stats import mannwhitneyu
from statsmodels.stats.multitest import multipletests


ROOT_DIR = Path(__file__).resolve().parent
DB_PATH = ROOT_DIR / "cell_counts.db"

FILTERED_OUTPUT_PATH = ROOT_DIR / "miraclib_melanoma_pbmc.csv"
SUBJECT_OUTPUT_PATH = ROOT_DIR / "miraclib_subject_level_summary.csv"
STATS_OUTPUT_PATH = ROOT_DIR / "miraclib_response_statistics.csv"
PLOT_OUTPUT_PATH = ROOT_DIR / "miraclib_response_boxplot.png"


def get_response_comparison_data(connection):
    """
    Query relative cell frequencies for melanoma PBMC samples
    from subjects treated with miraclib.
    """

    query = """
    SELECT
        s.sample,
        s.subject,
        s.project,
        s.condition,
        s.treatment,
        s.response,
        s.sample_type,
        s.time_from_treatment_start,
        p.population_name AS population,
        c.count,
        totals.total_count,
        100.0 * c.count / totals.total_count AS percentage
    FROM samples AS s

    JOIN cell_counts AS c
        ON s.sample = c.sample

    JOIN populations AS p
        ON c.population_id = p.population_id

    JOIN (
        SELECT
            sample,
            SUM(count) AS total_count
        FROM cell_counts
        GROUP BY sample
    ) AS totals
        ON s.sample = totals.sample

    WHERE LOWER(s.condition) = 'melanoma'
      AND LOWER(s.treatment) = 'miraclib'
      AND LOWER(s.sample_type) = 'pbmc'
      AND LOWER(s.response) IN ('yes', 'no')

    ORDER BY
        p.population_name,
        s.response,
        s.sample;
    """

    return pd.read_sql_query(query, connection)


def create_subject_summary(comparison):
    """
    Average each subject's relative frequency across repeated time points.
    """

    return (
        comparison
        .groupby(
            ["subject", "response", "population"],
            as_index=False
        )["percentage"]
        .mean()
        .rename(columns={"percentage": "mean_percentage"})
    )


def run_statistical_tests(subject_summary):
    """
    Compare responders and non-responders for each immune population
    using Mann-Whitney U tests and Benjamini-Hochberg correction (FDR)
    """

    results = []

    for population in subject_summary["population"].unique():

        population_data = subject_summary[
            subject_summary["population"] == population
        ]

        responders = population_data.loc[
            population_data["response"] == "yes",
            "mean_percentage"
        ]

        non_responders = population_data.loc[
            population_data["response"] == "no",
            "mean_percentage"
        ]

        statistic, p_value = mannwhitneyu(
            responders,
            non_responders,
            alternative="two-sided"
        )

        results.append(
            {
                "population": population,
                "responder_mean": responders.mean(),
                "non_responder_mean": non_responders.mean(),
                "difference": responders.mean() - non_responders.mean(),
                "u_statistic": statistic,
                "p_value": p_value,
            }
        )

    stats_results = pd.DataFrame(results)

    reject, adjusted_p_values, _, _ = multipletests(
        stats_results["p_value"],
        alpha=0.05,
        method="fdr_bh"
    )

    stats_results["significant_raw"] = stats_results["p_value"] < 0.05
    stats_results["adjusted_p_value"] = adjusted_p_values
    stats_results["significant_fdr"] = reject

    return stats_results


def print_data_summary(comparison):
    """
    Validation checks from the filtered datasets 
    """

    print(f"Filtered rows: {len(comparison)}")
    print(f"Unique samples: {comparison['sample'].nunique()}")
    print(f"Unique subjects: {comparison['subject'].nunique()}")

    print("\nSamples by response:")
    print(
        comparison[["sample", "response"]]
        .drop_duplicates()["response"]
        .value_counts()
    )

    print("\nSubjects by response:")
    print(
        comparison[["subject", "response"]]
        .drop_duplicates()["response"]
        .value_counts()
    )

    print("\nSamples per subject:")
    print(
        comparison[["subject", "sample"]]
        .drop_duplicates()
        .groupby("subject")
        .size()
        .value_counts()
        .sort_index()
    )

    print("\nAvailable time points:")
    print(
        comparison[["sample", "time_from_treatment_start"]]
        .drop_duplicates()["time_from_treatment_start"]
        .value_counts()
        .sort_index()
    )


def create_boxplot(subject_summary):
    """
    Create boxplots comparing responders and non-responders.
    """

    plt.figure(figsize=(12, 6))

    sns.boxplot(
        data=subject_summary,
        x="population",
        y="mean_percentage",
        hue="response"
    )

    plt.title(
        "Immune Cell Frequencies in Miraclib-Treated Melanoma Patients"
    )
    plt.xlabel("Immune cell population")
    plt.ylabel("Mean relative frequency (%)")

    plt.tight_layout()
    plt.savefig(PLOT_OUTPUT_PATH, dpi=300)
    plt.close()


def main():

    connection = sqlite3.connect(DB_PATH)

    try:
        # Query filtered sample-level data
        comparison = get_response_comparison_data(connection)
        comparison.to_csv(FILTERED_OUTPUT_PATH, index=False)

        print_data_summary(comparison)

        # Collapse repeated measurements to subject level
        subject_summary = create_subject_summary(comparison)
        subject_summary.to_csv(SUBJECT_OUTPUT_PATH, index=False)

        print("\nSubject-level summary:")
        print(subject_summary.head())
        print(f"\nSubject-level rows: {len(subject_summary)}")

        # Statistical comparison
        stats_results = run_statistical_tests(subject_summary)
        stats_results.to_csv(STATS_OUTPUT_PATH, index=False)

        print("\nResponder vs non-responder statistical comparison:")
        print(stats_results)

        # Visualization
        create_boxplot(subject_summary)

        print("\nOutputs created:")
        print(f"- {FILTERED_OUTPUT_PATH.name}")
        print(f"- {SUBJECT_OUTPUT_PATH.name}")
        print(f"- {STATS_OUTPUT_PATH.name}")
        print(f"- {PLOT_OUTPUT_PATH.name}")

    finally:
        connection.close()


if __name__ == "__main__":
    main()