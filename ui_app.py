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
st.title("🚀 JIRA Release Tracker")

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

# Tabs
released_tab, unreleased_tab = st.tabs(["📦 Released", "🛠️ Unreleased"])

with released_tab:
    selected_released = st.selectbox("Select Released Version", released_versions, key="released_ver")
    if selected_released:
        jira_df = load_jira_issues(selected_released).copy()
        db_df = load_from_db(selected_released)

        jira_df.columns = jira_df.columns.str.strip()
        db_df.columns = db_df.columns.str.strip()
        jira_df.rename(columns={"JIRA": "jira_key"}, inplace=True)

        if not db_df.empty:
            custom_db_cols = editable_cols + ["jira_key"]
            db_trimmed = db_df[custom_db_cols].copy()
            merged_df = pd.merge(jira_df, db_trimmed, how="left", on="jira_key")
            for col in editable_cols:
                if col not in merged_df.columns:
                    merged_df[col] = ""
            final_cols = [col for col in jira_df.columns if col != "jira_key"] + editable_cols
            st.data_editor(merged_df[final_cols], key="released_data", use_container_width=True, disabled=[
                "Team Name", "JIRA", "JIRA Type", "Assignee"])
        else:
            for col in editable_cols:
                if col not in jira_df.columns:
                    jira_df[col] = ""
            final_cols = [col for col in jira_df.columns if col != "jira_key"] + editable_cols
            st.data_editor(jira_df[final_cols], key="released_data_empty", use_container_width=True, disabled=[
                "Team Name", "JIRA", "JIRA Type", "Assignee"])

with unreleased_tab:
    selected_unreleased = st.selectbox("Select Unreleased Version", unreleased_versions, key="unreleased_ver")
    if selected_unreleased:
        if st.session_state.loaded_version != selected_unreleased or st.session_state.editable_df.empty:
            jira_df = load_jira_issues(selected_unreleased).copy()
            db_df = load_from_db(selected_unreleased)

            jira_df.columns = jira_df.columns.str.strip()
            db_df.columns = db_df.columns.str.strip()
            jira_df.rename(columns={"JIRA": "jira_key"}, inplace=True)

            if not db_df.empty:
                custom_db_cols = editable_cols + ["jira_key"]
                db_trimmed = db_df[custom_db_cols].copy()
                merged_df = pd.merge(jira_df, db_trimmed, how="left", on="jira_key")
                for col in editable_cols:
                    if col not in merged_df.columns:
                        merged_df[col] = ""
                final_cols = [col for col in jira_df.columns if col != "jira_key"] + editable_cols
                st.session_state.editable_df = merged_df[final_cols]
            else:
                for col in editable_cols:
                    if col not in jira_df.columns:
                        jira_df[col] = ""
                final_cols = [col for col in jira_df.columns if col != "jira_key"] + editable_cols
                st.session_state.editable_df = jira_df[final_cols]

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
        submitted = st.form_submit_button("💾 Save & Update JIRA")

    if submitted:
        for col in editable_cols:
            if col not in temp_df.columns:
                temp_df[col] = ""
        st.session_state.temp_save = temp_df
        st.session_state.show_confirm = True

    if st.session_state.get("show_confirm") and "temp_save" in st.session_state:
        with st.expander("⚠️ Confirm Save Operation", expanded=True):
            st.write("Are you sure you want to save changes to the database and update JIRA?")
            col1, col2 = st.columns([1, 1])
            if col1.button("✅ Confirm Save"):
                save_to_db(st.session_state.temp_save, selected_unreleased)
                update_jira_fields(st.session_state.temp_save)
                st.success("✅ Data saved to DB and JIRA updated successfully.")
                st.session_state.editable_df = st.session_state.temp_save
                st.session_state.show_confirm = False
                del st.session_state.temp_save
            if col2.button("❌ Cancel"):
                st.session_state.show_confirm = False
                del st.session_state.temp_save
