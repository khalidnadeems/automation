import streamlit as st
import pandas as pd
from helpers import (
    create_table_if_not_exists,
    get_versions,
    load_from_db,
    get_issues_by_fix_version,
    save_to_db,
    update_jira_fields
)

st.set_page_config(page_title="JIRA Release Dashboard", layout="wide")
st.title("ðŸš€ JIRA Release Tracker")

create_table_if_not_exists()

released_versions, unreleased_versions = get_versions()

if "loaded_version" not in st.session_state:
    st.session_state.loaded_version = None
if "editable_df" not in st.session_state:
    st.session_state.editable_df = pd.DataFrame()
if "show_confirm" not in st.session_state:
    st.session_state.show_confirm = False

editable_cols = [
    "Story Type",
    "User Sign-off Needed? Y/N",
    "Release Component",
    "Justification for Release",
    "Pre-Implementation Plan",
    "Implementation Plan",
    "Post Implementation Plan",
    "Risk / Impact if not released",
    "Rollback Plan"
]

@st.cache_data
def load_jira_issues(version):
    return get_issues_by_fix_version(version)

released_tab, unreleased_tab = st.tabs(["ðŸ“¦ Released", "ðŸ› ï¸ Unreleased"])

def normalize_keys(df, col):
    return df[col].astype(str).str.strip().str.upper()

with released_tab:
    selected_released = st.selectbox("Select Released Version", released_versions, key="released_ver")
    if selected_released:
        jira_df = load_jira_issues(selected_released).copy()
        db_df = load_from_db(selected_released)

        jira_df.columns = jira_df.columns.str.strip()
        db_df.columns = db_df.columns.str.strip()

        if "JIRA" in jira_df.columns:
            jira_df["jira_key"] = normalize_keys(jira_df, "JIRA")
        if "jira_key" not in db_df.columns and "JIRA" in db_df.columns:
            db_df["jira_key"] = normalize_keys(db_df, "JIRA")
        else:
            db_df["jira_key"] = normalize_keys(db_df, "jira_key")

        for col in editable_cols:
            if col not in db_df.columns:
                db_df[col] = ""

        custom_db_cols = editable_cols + ["jira_key"]
        db_trimmed = db_df[custom_db_cols].copy()

        merged_df = pd.merge(jira_df, db_trimmed, how="left", on="jira_key")
        for col in editable_cols:
            if col not in merged_df.columns:
                merged_df[col] = ""

        jira_core_cols = [col for col in jira_df.columns if col not in editable_cols and col != "jira_key"]
        final_cols = jira_core_cols + editable_cols

        released_data = st.data_editor(merged_df[final_cols], key="released_data", use_container_width=True, disabled=[
            "Team Name", "JIRA", "JIRA Type", "Assignee"])
        if st.button("ðŸ’¾ Save Released Data"):
            save_to_db(released_data, selected_released)
            st.success("âœ… Released data saved to database successfully.")

with unreleased_tab:
    selected_unreleased = st.selectbox("Select Unreleased Version", unreleased_versions, key="unreleased_ver")
    if selected_unreleased:
        if st.session_state.loaded_version != selected_unreleased or st.session_state.editable_df.empty:
            jira_df = load_jira_issues(selected_unreleased).copy()
            db_df = load_from_db(selected_unreleased)

            jira_df.columns = jira_df.columns.str.strip()
            db_df.columns = db_df.columns.str.strip()

            if "JIRA" in jira_df.columns:
                jira_df["jira_key"] = normalize_keys(jira_df, "JIRA")
            if "jira_key" not in db_df.columns and "JIRA" in db_df.columns:
                db_df["jira_key"] = normalize_keys(db_df, "JIRA")
            else:
                db_df["jira_key"] = normalize_keys(db_df, "jira_key")

            for col in editable_cols:
                if col not in db_df.columns:
                    db_df[col] = ""

            custom_db_cols = editable_cols + ["jira_key"]
            db_trimmed = db_df[custom_db_cols].copy()

            merged_df = pd.merge(jira_df, db_trimmed, how="left", on="jira_key")
            for col in editable_cols:
                if col not in merged_df.columns:
                    merged_df[col] = ""

            jira_core_cols = [col for col in jira_df.columns if col not in editable_cols and col != "jira_key"]
            final_cols = jira_core_cols + editable_cols

            st.session_state.editable_df = merged_df[final_cols]
            st.session_state.loaded_version = selected_unreleased
            st.session_state.show_confirm = False

    with st.form(key="edit_form"):
        temp_df = st.data_editor(
            st.session_state.editable_df,
            key="edit_unreleased",
            use_container_width=True,
            num_rows="dynamic",
            disabled=["Team Name", "JIRA", "JIRA Type", "Assignee"]
        )
        submitted = st.form_submit_button("ðŸ’¾ Save & Update JIRA")

    if submitted:
        for col in editable_cols:
            if col not in temp_df.columns:
                temp_df[col] = ""
        st.session_state.temp_save = temp_df
        st.session_state.show_confirm = True

    if st.session_state.get("show_confirm") and "temp_save" in st.session_state:
        with st.expander("âš ï¸ Confirm Save Operation", expanded=True):
            st.write("Are you sure you want to save changes to the database and update JIRA?")
            col1, col2 = st.columns([1, 1])
            if col1.button("âœ… Confirm Save"):
                save_to_db(st.session_state.temp_save, selected_unreleased)
                update_jira_fields(st.session_state.temp_save)
                st.success("âœ… Data saved to DB and JIRA updated successfully.")
                st.session_state.editable_df = st.session_state.temp_save
                st.session_state.show_confirm = False
                del st.session_state.temp_save
            if col2.button("âŒ Cancel"):
                st.session_state.show_confirm = False
                del st.session_state.temp_save
