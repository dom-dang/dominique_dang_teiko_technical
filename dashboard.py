from pathlib import Path

import pandas as pd
import streamlit as st


ROOT_DIR = Path(__file__).resolve().parent

PART2_PATH = ROOT_DIR / "cell_frequency_summary.csv"
PART3_SUBJECT_PATH = ROOT_DIR / "miraclib_subject_level_summary.csv"
PART3_STATS_PATH = ROOT_DIR / "miraclib_response_statistics.csv"
PART3_PLOT_PATH = ROOT_DIR / "miraclib_response_boxplot.png"

PART4_BASELINE_PATH = ROOT_DIR / "miraclib_melanoma_pbmc_baseline.csv"
PART4_PROJECT_PATH = ROOT_DIR / "baseline_samples_by_project.csv"
PART4_RESPONSE_PATH = ROOT_DIR / "baseline_subjects_by_response.csv"
PART4_SEX_PATH = ROOT_DIR / "baseline_subjects_by_sex.csv"


st.set_page_config(
    page_title="Teiko Technical Dashboard",
    layout="wide",
)


@st.cache_data
def load_csv(path):
    return pd.read_csv(path)

part2 = load_csv(PART2_PATH)
part3_subject = load_csv(PART3_SUBJECT_PATH)
part3_stats = load_csv(PART3_STATS_PATH)

part4_baseline = load_csv(PART4_BASELINE_PATH)
part4_project = load_csv(PART4_PROJECT_PATH)
part4_response = load_csv(PART4_RESPONSE_PATH)
part4_sex = load_csv(PART4_SEX_PATH)


st.title("Loblaw Bio Immune Cell Analysis")

st.write(
    "Interactive overview of immune-cell frequencies, "
    "miraclib response comparisons, and baseline melanoma PBMC samples."
)


tab1, tab2, tab3 = st.tabs(
    [
        "Step 2: Cell Frequencies",
        "Step 3: Response Analysis",
        "Step 4: Baseline Subset",
    ]
)


# Step 2
with tab1:
    st.header("Cell Population Relative Frequencies")

    st.write(
        "Each row represents one immune-cell population from one sample."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Samples",
            f"{part2['sample'].nunique():,}"
        )

    with col2:
        st.metric(
            "Cell populations",
            part2["population"].nunique()
        )

    selected_sample = st.selectbox(
        "Select a sample",
        sorted(part2["sample"].unique())
    )

    sample_data = part2[
        part2["sample"] == selected_sample
    ].copy()

    st.subheader(f"Cell frequencies for {selected_sample}")

    st.dataframe(
        sample_data,
        use_container_width=True,
        hide_index=True,
    )

    chart_data = (
        sample_data[
            ["population", "percentage"]
        ]
        .set_index("population")
    )

    st.bar_chart(chart_data)


# Step 3
with tab2:

    st.header("Miraclib Response Analysis")

    st.write(
        "Comparison of melanoma PBMC subjects receiving miraclib, "
        "grouped by responder status."
    )

    responders = (
        part3_subject[
            part3_subject["response"] == "yes"
        ]["subject"]
        .nunique()
    )

    non_responders = (
        part3_subject[
            part3_subject["response"] == "no"
        ]["subject"]
        .nunique()
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Responders",
            responders
        )

    with col2:
        st.metric(
            "Non-responders",
            non_responders
        )

    st.subheader("Responder vs non-responder boxplots")

    st.image(
        str(PART3_PLOT_PATH),
        use_container_width=True
    )

    st.subheader("Statistical results")

    stats_display = part3_stats.copy()

    stats_display["responder_mean"] = (
        stats_display["responder_mean"].round(2)
    )

    stats_display["non_responder_mean"] = (
        stats_display["non_responder_mean"].round(2)
    )

    stats_display["difference"] = (
        stats_display["difference"].round(2)
    )

    stats_display["p_value"] = (
        stats_display["p_value"].round(4)
    )

    stats_display["adjusted_p_value"] = (
        stats_display["adjusted_p_value"].round(4)
    )

    st.dataframe(
        stats_display,
        use_container_width=True,
        hide_index=True,
    )

    st.info(
        "CD4 T cells showed a nominal difference between responders "
        "and non-responders, but the result did not remain significant "
        "after Benjamini-Hochberg multiple-testing correction."
    )

    st.subheader("Explore one immune population")

    selected_population = st.selectbox(
        "Population",
        sorted(part3_subject["population"].unique()),
        key="part3_population"
    )

    population_data = part3_subject[
        part3_subject["population"] == selected_population
    ]

    st.dataframe(
        population_data,
        use_container_width=True,
        hide_index=True,
    )

# Step 4
with tab3:

    st.header("Baseline Melanoma PBMC Miraclib Samples")

    st.write(
        "Baseline samples have time_from_treatment_start = 0."
    )

    total_samples = len(part4_baseline)
    total_subjects = part4_baseline["subject"].nunique()

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Baseline samples",
            total_samples
        )

    with col2:
        st.metric(
            "Unique subjects",
            total_subjects
        )

    st.subheader("Samples by project")

    st.dataframe(
        part4_project,
        use_container_width=True,
        hide_index=True,
    )

    st.bar_chart(
        part4_project.set_index("project")
    )

    st.subheader("Subjects by response")

    st.dataframe(
        part4_response,
        use_container_width=True,
        hide_index=True,
    )

    st.bar_chart(
        part4_response.set_index("response")
    )

    st.subheader("Subjects by sex")

    st.dataframe(
        part4_sex,
        use_container_width=True,
        hide_index=True,
    )

    st.bar_chart(
        part4_sex.set_index("sex")
    )

    st.subheader("Baseline sample table")

    project_filter = st.multiselect(
        "Filter by project",
        sorted(part4_baseline["project"].unique()),
        default=sorted(part4_baseline["project"].unique())
    )

    response_filter = st.multiselect(
        "Filter by response",
        sorted(part4_baseline["response"].unique()),
        default=sorted(part4_baseline["response"].unique())
    )

    sex_filter = st.multiselect(
        "Filter by sex",
        sorted(part4_baseline["sex"].unique()),
        default=sorted(part4_baseline["sex"].unique())
    )

    filtered_baseline = part4_baseline[
        part4_baseline["project"].isin(project_filter)
        & part4_baseline["response"].isin(response_filter)
        & part4_baseline["sex"].isin(sex_filter)
    ]

    st.write(
        f"Showing {len(filtered_baseline):,} samples."
    )

    st.dataframe(
        filtered_baseline,
        use_container_width=True,
        hide_index=True,
    )