
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

tab1, tab2 = st.tabs(["ðŸ“¦ Released", "ðŸ› ï¸ Unreleased"])

with tab1:
    selected_released = st.selectbox("Select Released Version", released_versions, key="released_ver")
    if selected_released:
        df = load_from_db(selected_released)
        if df.empty:
            st.warning("No saved data found for this release.")
        else:
            st.data_editor(df, key="released_view", use_container_width=True, disabled=[
                "Team Name", "JIRA", "JIRA Type", "Assignee"])

with tab2:
    selected_unreleased = st.selectbox("Select Unreleased Version", unreleased_versions, key="unreleased_ver")

    if "loaded_version" not in st.session_state or st.session_state.loaded_version != selected_unreleased:
        st.session_state.loaded_version = selected_unreleased
        st.session_state.editable_df = get_issues_by_fix_version(selected_unreleased)
        st.session_state.show_confirm = False

    st.session_state.editable_df = st.data_editor(
        st.session_state.editable_df,
        key="edit_unreleased",
        use_container_width=True,
        num_rows="dynamic",
        disabled=["Team Name", "JIRA", "JIRA Type", "Assignee"]
    )

    if st.button("ðŸ’¾ Save & Update JIRA"):
        st.session_state.show_confirm = True

    if st.session_state.get("show_confirm"):
        with st.expander("âš ï¸ Confirm Save Operation", expanded=True):
            st.write("Are you sure you want to save changes to the database and update JIRA?")
            col1, col2 = st.columns([1, 1])
            if col1.button("âœ… Confirm Save"):
                save_to_db(st.session_state.editable_df, selected_unreleased)
                update_jira_fields(st.session_state.editable_df)
                st.success("âœ… Data saved to DB and JIRA updated successfully.")
                st.session_state.show_confirm = False
            if col2.button("âŒ Cancel"):
                st.session_state.show_confirm = False
