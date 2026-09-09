# Teiko Technical 

This project analyzes immune cell population data from a clinical trial using Python, SQLite, statistical testing, and Streamlit.

The workflow covers:

- loading the raw CSV into a relational SQLite database
- calculating immune-cell relative frequencies for each sample
- comparing miraclib responders vs non-responders in melanoma PBMC samples
- performing statistical testing with multiple-testing correction
- analyzing baseline melanoma PBMC samples treated with miraclib
- displaying Parts 2–4 in an interactive Streamlit dashboard

## Project Structure

```text
.
├── cell-count.csv
├── cell_counts.db
├── load_data.py
├── step2_analyze.py
├── step3_compare_response.py
├── step4_subset_analysis.py
├── dashboard.py
├── Makefile
├── requirements.txt
├── README.md
├── cell_frequency_summary.csv
├── miraclib_melanoma_pbmc.csv
├── miraclib_subject_level_summary.csv
├── miraclib_response_statistics.csv
├── miraclib_response_boxplot.png
├── miraclib_melanoma_pbmc_baseline.csv
├── baseline_samples_by_project.csv
├── baseline_subjects_by_response.csv
└── baseline_subjects_by_sex.csv
````

## Setup

The project is designed to run in GitHub Codespaces or another environment with Python 3 installed.

Install all required dependencies with:

```bash
make setup
```

This creates a local Python virtual environment in `.venv` and installs the packages listed in `requirements.txt`.

## Run the Full Pipeline

Run the complete pipeline with:

```bash
make pipeline
```

This executes the following steps sequentially:

1. `load_data.py`

   * creates the SQLite database
   * creates the database schema
   * loads all rows from `cell-count.csv`

2. `step2_analyze.py`

   * calculates the total cell count for each sample
   * calculates the relative frequency of each immune-cell population
   * writes the Step 2 summary table

3. `step3_compare_response.py`

   * filters melanoma PBMC samples from subjects treated with miraclib
   * compares responders and non-responders
   * accounts for repeated samples by averaging measurements at the subject level
   * performs Mann-Whitney U tests
   * applies Benjamini-Hochberg false-discovery-rate correction
   * creates responder vs non-responder boxplots

4. `step4_subset_analysis.py`

   * identifies baseline melanoma PBMC samples treated with miraclib
   * summarizes samples by project
   * summarizes subjects by response
   * summarizes subjects by sex

## Run the Dashboard

After running the pipeline, start the interactive dashboard with:

```bash
make dashboard
```

The Streamlit application displays:

* Step 2 cell-frequency summaries
* Step 3 responder vs non-responder analysis
* statistical results and boxplots
* Step 4 baseline subset summaries and filters

For local use, Streamlit will display a local URL after running `make dashboard`.

---

# Database Schema

The SQLite database contains three main tables:

## `samples`

Stores metadata for each biological sample.

Important fields include:

* `sample`
* `project`
* `subject`
* `condition`
* `age`
* `sex`
* `treatment`
* `response`
* `sample_type`
* `time_from_treatment_start`

The `sample` field is the primary key.

## `populations`

Stores the immune-cell population definitions.

The five populations in the supplied dataset are:

* `b_cell`
* `cd8_t_cell`
* `cd4_t_cell`
* `nk_cell`
* `monocyte`

Each population is assigned a unique `population_id`.

## `cell_counts`

Stores the measured cell count for each population in each sample.

Important fields are:

* `sample`
* `population_id`
* `count`

The combination of `sample` and `population_id` is the primary key.

Foreign keys connect `cell_counts` to the `samples` and `populations` tables.

## Schema Design Rationale

The source CSV stores the five immune populations in separate columns. During loading, these columns are converted from wide format into a normalized long-format measurement table.

For example, source data conceptually stored as:

```text
sample | b_cell | cd8_t_cell | cd4_t_cell | nk_cell | monocyte
```

becomes:

```text
sample | population_id | count
```

This design separates sample metadata from immune-cell measurements and avoids requiring a database schema change whenever a new immune-cell population is introduced.

It also makes common analytical operations easier, including:

* grouping by immune-cell population
* calculating sample totals
* calculating relative frequencies
* comparing population frequencies across clinical groups
* adding future populations without creating additional measurement columns

The current schema keeps the project simple while retaining a structure that can be extended to larger datasets and additional analytics.

---

# Part 2: Relative Cell Frequencies

For every sample, the total cell count is calculated as the sum of:

* B cells
* CD8 T cells
* CD4 T cells
* NK cells
* monocytes

The relative frequency of each population is then calculated as:

```text
percentage = population count / total sample count × 100
```

The resulting output contains:

* `sample`
* `total_count`
* `population`
* `count`
* `percentage`

The output is saved as:

```text
cell_frequency_summary.csv
```

---

# Part 3: Miraclib Response Analysis

The responder analysis includes only samples meeting all of the following criteria:

* melanoma
* PBMC
* treatment = miraclib
* response = yes or no

The filtered dataset contains repeated measurements at treatment days 0, 7, and 14.

Because measurements from the same subject are not statistically independent, the three time points are averaged for each subject and immune-cell population before comparing responders and non-responders.

This produces one mean relative-frequency value per:

```text
subject × immune-cell population
```

## Statistical Method

Responder and non-responder distributions are compared separately for each immune-cell population using a two-sided Mann-Whitney U test.

Five population-level hypotheses are tested, so Benjamini-Hochberg false-discovery-rate correction is applied to the resulting p-values.

The analysis showed a nominal difference in CD4 T-cell relative frequency:

* responders: approximately 30.54%
* non-responders: approximately 29.90%
* unadjusted p-value: approximately 0.0124

However, after Benjamini-Hochberg correction:

```text
adjusted p-value ≈ 0.0621
```

Therefore, no immune-cell population remained statistically significant at an FDR threshold of 0.05.

This means the observed CD4 T-cell difference may be suggestive, but the current analysis does not provide sufficient evidence to conclude that any of the five populations independently predicts miraclib response.

Outputs include:

```text
miraclib_melanoma_pbmc.csv
miraclib_subject_level_summary.csv
miraclib_response_statistics.csv
miraclib_response_boxplot.png
```

---

# Part 4: Baseline Subset Analysis

The baseline subset contains samples meeting all of the following criteria:

* melanoma
* PBMC
* treatment = miraclib
* `time_from_treatment_start = 0`

The resulting subset contains:

```text
656 baseline samples
656 unique subjects
```

## Samples by Project

```text
prj1: 384
prj3: 272
```

## Subjects by Response

```text
Responders: 331
Non-responders: 325
```

## Subjects by Sex

```text
Female: 312
Male: 344
```

Outputs include:

```text
miraclib_melanoma_pbmc_baseline.csv
baseline_samples_by_project.csv
baseline_subjects_by_response.csv
baseline_subjects_by_sex.csv
```

