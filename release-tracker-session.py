import streamlit as st
import pandas as pd
import pyodbc
import requests
from jira import JIRA
from jira.resilientsession import ResilientSession

# ---- CONFIG ----
JIRA_URL = "https://your-domain.atlassian.net"
JIRA_EMAIL = "your-email@example.com"
JIRA_API_TOKEN = "your-api-token"
JIRA_PROJECT_KEY = "ABC"

SQL_SERVER = "your_sql_server"
SQL_DB = "your_database"
TABLE_NAME = "JiraReleaseDetails"

# ---- PATCH for JIRA Bug ----
if not hasattr(ResilientSession, "max_retries"):
    ResilientSession.max_retries = 3

# ---- DB FUNCTIONS ----
def get_connection():
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={SQL_DB};"
        "Trusted_Connection=yes;"
    )
    return pyodbc.connect(conn_str)

def create_table_if_not_exists():
    query = f"""
    IF NOT EXISTS (
        SELECT * FROM sysobjects WHERE name='{TABLE_NAME}' AND xtype='U'
    )
    CREATE TABLE {TABLE_NAME} (
        team_name NVARCHAR(255),
        jira_key NVARCHAR(100),
        jira_type NVARCHAR(100),
        assignee NVARCHAR(100),
        summary NVARCHAR(MAX),
        business_benefit NVARCHAR(MAX),
        story_type NVARCHAR(50),
        user_signoff NVARCHAR(5),
        release_component NVARCHAR(255),
        justification NVARCHAR(MAX),
        pre_plan NVARCHAR(MAX),
        impl_plan NVARCHAR(MAX),
        post_plan NVARCHAR(MAX),
        risk_impact NVARCHAR(MAX),
        rollback_plan NVARCHAR(MAX),
        fix_version NVARCHAR(100)
    )"""
    conn = get_connection()
    conn.execute(query)
    conn.commit()
    conn.close()

def save_to_db(df, version):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE fix_version = ?", version)
    for _, row in df.iterrows():
        cursor.execute(f"""
            INSERT INTO {TABLE_NAME} (
                team_name, jira_key, jira_type, assignee, summary, business_benefit,
                story_type, user_signoff, release_component, justification,
                pre_plan, impl_plan, post_plan, risk_impact, rollback_plan, fix_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row['Team Name'], row['JIRA'], row['JIRA Type'], row['Assignee'], row['Summary'], row['Business Benefit'],
            row.get('Story Type', ''), row.get('User Sign-off Needed?', ''), row.get('Release Component', ''),
            row.get('Justification for Release', ''), row.get('Pre-Implementation Plan', ''),
            row.get('Implementation Plan', ''), row.get('Post Implementation Plan', ''),
            row.get('Risk / Impact if not released', ''), row.get('Rollback Plan', ''), version
        ))
    conn.commit()
    conn.close()

def update_jira_fields(df):
    jira = get_jira_connection()
    for _, row in df.iterrows():
        try:
            issue = jira.issue(row['JIRA'])
            fields_to_update = {}
            if row['Summary'] != issue.fields.summary:
                fields_to_update['summary'] = row['Summary']
            # Assuming 'Business Benefit' is mapped to a customfield
            if hasattr(issue.fields, 'customfield_XXXXX') and row['Business Benefit'] != getattr(issue.fields, 'customfield_XXXXX'):
                fields_to_update['customfield_XXXXX'] = row['Business Benefit']
            if fields_to_update:
                issue.update(fields=fields_to_update)
        except Exception as e:
            st.error(f"Failed to update JIRA {row['JIRA']}: {e}")

# ---- JIRA FUNCTIONS ----
@st.cache_data(ttl=300)
def get_jira_connection():
    return JIRA(options={"server": JIRA_URL}, basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN))

@st.cache_data(ttl=300)
def get_versions():
    jira = get_jira_connection()
    versions = jira.project_versions(JIRA_PROJECT_KEY)
    return [v.name for v in versions if v.released], [v.name for v in versions if not v.released]

def get_issues_by_fix_version(version):
    jira = get_jira_connection()
    issues = jira.search_issues(f'project = {JIRA_PROJECT_KEY} AND fixVersion = "{version}"', maxResults=1000)
    data = []
    for issue in issues:
        data.append({
            "Team Name": issue.fields.customfield_XXXXX if hasattr(issue.fields, 'customfield_XXXXX') else "",  # Replace with actual field if needed
            "JIRA": issue.key,
            "JIRA Type": issue.fields.issuetype.name,
            "Assignee": issue.fields.assignee.displayName if issue.fields.assignee else "",
            "Summary": issue.fields.summary,
            "Business Benefit": "",
            "Story Type": "",
            "User Sign-off Needed?": "",
            "Release Component": "",
            "Justification for Release": "",
            "Pre-Implementation Plan": "",
            "Implementation Plan": "",
            "Post Implementation Plan": "",
            "Risk / Impact if not released": "",
            "Rollback Plan": ""
        })
    return pd.DataFrame(data)

# ---- UI ----
st.set_page_config(page_title="JIRA Release Tracker", layout="wide")
st.title("🚀 JIRA Release Dashboard")

create_table_if_not_exists()
released_versions, unreleased_versions = get_versions()

tab1, tab2 = st.tabs(["📦 Released", "🛠️ Unreleased"])

with tab1:
    selected = st.selectbox("Select Released Version", released_versions)
    if selected:
        df = load_from_db(selected)
        if df.empty:
            st.warning("No data found.")
        else:
            st.data_editor(df, key="released_view", use_container_width=True, disabled=["Team Name", "JIRA", "JIRA Type", "Assignee"])

with tab2:
    selected = st.selectbox("Select Unreleased Version", unreleased_versions)
    if selected:
        df = get_issues_by_fix_version(selected)
        editable_df = st.data_editor(
            df, key="unreleased_edit", use_container_width=True,
            disabled=["Team Name", "JIRA", "JIRA Type", "Assignee"], num_rows="dynamic"
        )
        if st.button("💾 Save to SQL and Update JIRA"):
            save_to_db(editable_df, selected)
            update_jira_fields(editable_df)
            st.success("Saved and JIRA updated successfully!")
