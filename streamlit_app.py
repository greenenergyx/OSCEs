import os
import random
import re
import pandas as pd
import streamlit as st

DEFAULT_DATA_DIR = "/content/drive/MyDrive/Gem"
XLSX_NAME = "Radiopaedia_Library.xlsx"
CSV_NAME = "sample_radiopedia_articles.csv"

st.set_page_config(
    page_title="Radiology OSCE Case Generator",
    page_icon="🩺",
    layout="wide",
)


def load_dataframe_from_excel(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)
    return df


def load_dataframe_from_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    required_columns = [
        "rid",
        "title",
        "system",
        "section",
        "url",
        "remote_last_mod_date",
        "content",
    ]
    for col in required_columns:
        if col not in df.columns:
            df[col] = ""
    return df[required_columns].copy()


def extract_case_findings(row: pd.Series) -> str:
    content = str(row.get("content", ""))
    if not content.strip():
        return "Review the case content and describe the key imaging findings."

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\\s+", content) if s.strip()]
    if sentences:
        return sentences[0]
    return content[:200]


def build_marking_grid() -> pd.DataFrame:
    rubric = [
        {"Criteria": "Anatomy / Clinical context", "Points": 2, "Notes": "Clear description of location and presenting features."},
        {"Criteria": "Key imaging finding", "Points": 2, "Notes": "Identifies the most important radiologic abnormality."},
        {"Criteria": "Differential diagnosis", "Points": 2, "Notes": "Provides a relevant differential."},
        {"Criteria": "Management / next step", "Points": 2, "Notes": "Recommends an appropriate next step or management plan."},
    ]
    return pd.DataFrame(rubric)


def generate_osce_case(article: pd.Series, case_number: int, custom_notes: str, include_grid: bool) -> dict:
    title = str(article.get("title", "Untitled case")).strip()
    system = str(article.get("system", "General radiology")).strip()
    section = str(article.get("section", "")).strip()
    content = str(article.get("content", "")).strip()
    url = str(article.get("url", "")).strip()
    rid = str(article.get("rid", "")).strip()

    scenario = (
        f"Case {case_number}: A patient presents with a radiology case involving {system}. "
        f"Use the article title '{title}' as the central clinical theme."
    )
    if section:
        scenario += f" The case sits within the section: {section}."

    findings_prompt = extract_case_findings(article)
    hidden_answer = (
        f"Diagnosis: {title}\n"
        f"Key imaging findings: {findings_prompt}\n"
        f"Radiopaedia URL: {url}\n"
        f"Suggested differential: consider {system} abnormalities and descriptive imaging features."
    )

    if custom_notes:
        hidden_answer += f"\nReference notes: {custom_notes}"

    case = {
        "case_id": case_number,
        "scenario": scenario,
        "question": (
            "Describe the most likely diagnosis based on the imaging, list your top differential diagnoses, "
            "and suggest the next best management step."
        ),
        "findings": findings_prompt,
        "hidden_answer": hidden_answer,
        "marking_grid": build_marking_grid() if include_grid else None,
        "source_url": url,
        "rid": rid,
    }

    return case


def render_case(case: dict):
    st.subheader(f"🧠 OSCE Case #{case['case_id']}")
    st.write(case["scenario"])
    st.info(case["question"])
    st.markdown("**Key imaging prompt:**")
    st.write(case["findings"])

    reveal_key = f"reveal_answer_{case['case_id']}"
    if reveal_key not in st.session_state:
        st.session_state[reveal_key] = False

    if st.button("Reveal answer", key=reveal_key):
        st.session_state[reveal_key] = True

    if st.session_state[reveal_key]:
        with st.expander("Answer & teaching points", expanded=True):
            st.write(case["hidden_answer"])
            if case["marking_grid"] is not None:
                st.markdown("**Marking grid**")
                st.table(case["marking_grid"])

    st.markdown("---")


@st.cache_data
def load_data_paths(data_dir: str, excel_uploaded, csv_uploaded):
    excel_df = None
    csv_df = None
    problems = []

    if excel_uploaded is not None:
        try:
            excel_df = load_dataframe_from_excel(excel_uploaded)
        except Exception as exc:
            problems.append(f"Excel upload failed: {exc}")

    else:
        excel_path = os.path.join(data_dir, XLSX_NAME)
        if os.path.exists(excel_path):
            try:
                excel_df = load_dataframe_from_excel(excel_path)
            except Exception as exc:
                problems.append(f"Could not load Excel from {excel_path}: {exc}")

    if csv_uploaded is not None:
        try:
            csv_df = load_dataframe_from_csv(csv_uploaded)
        except Exception as exc:
            problems.append(f"CSV upload failed: {exc}")

    else:
        csv_path = os.path.join(data_dir, CSV_NAME)
        if os.path.exists(csv_path):
            try:
                csv_df = load_dataframe_from_csv(csv_path)
            except Exception as exc:
                problems.append(f"Could not load CSV from {csv_path}: {exc}")

    return excel_df, csv_df, problems


def main():
    st.title("Radiology OSCE Case Generator")
    st.write(
        "Generate interactive radiology OSCE-style cases from your Radiopaedia library and sample cases. "
        "Use the hidden-answer reveal buttons and optional marking grid for teaching or exam practice."
    )

    with st.sidebar:
        st.header("Data sources")
        data_dir = st.text_input("Default data folder", DEFAULT_DATA_DIR)
        excel_file = st.file_uploader("Upload Radiopaedia_Library.xlsx", type=["xlsx"])
        csv_file = st.file_uploader("Upload sample_radiopedia_articles.csv", type=["csv"])
        st.markdown("---")
        st.header("Case generation")
        num_cases = st.number_input("Number of cases", min_value=1, max_value=20, value=3)
        system_filter = st.text_input("Filter by system keyword", value="")
        custom_notes = st.text_area("Reference / enrichment notes", help="Add any guidance from your radiology books or notes.")
        include_grid = st.checkbox("Include marking grid", value=True)
        generate_button = st.button("Generate OSCE cases")

    excel_df, csv_df, problems = load_data_paths(data_dir, excel_file, csv_file)
    if problems:
        for problem in problems:
            st.warning(problem)

    has_data = excel_df is not None or csv_df is not None
    if not has_data:
        st.warning(
            "No data loaded. Please upload an Excel/CSV file or place the files in the default folder. "
            "The app can use either the Radiopaedia library Excel or sample CSV to generate cases."
        )
        st.stop()

    data_df = None
    if csv_df is not None:
        data_df = normalize_dataframe(csv_df)
    elif excel_df is not None:
        data_df = normalize_dataframe(excel_df)

    if data_df is None or data_df.empty:
        st.error("Loaded data is empty or could not be normalized.")
        st.stop()

    if generate_button:
        if system_filter:
            filtered_df = data_df[data_df["system"].str.contains(system_filter, case=False, na=False)]
        else:
            filtered_df = data_df

        if filtered_df.empty:
            st.error("No cases match the selected system filter.")
            st.stop()

        selected = filtered_df.sample(min(int(num_cases), len(filtered_df)), random_state=random.randint(0, 9999))
        selected = selected.reset_index(drop=True)

        generated_cases = []
        for i, row in selected.iterrows():
            generated_cases.append(
                generate_osce_case(row, i + 1, custom_notes, include_grid)
            )

        st.success(f"Generated {len(generated_cases)} OSCE cases.")

        for case in generated_cases:
            render_case(case)

        download_df = pd.DataFrame([
            {
                "case_id": case["case_id"],
                "scenario": case["scenario"],
                "question": case["question"],
                "findings": case["findings"],
                "answer": case["hidden_answer"],
                "source_url": case["source_url"],
            }
            for case in generated_cases
        ])

        csv_bytes = download_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download generated cases as CSV",
            data=csv_bytes,
            file_name="radiology_osce_cases.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
