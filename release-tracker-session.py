import streamlit as st
import pandas as pd
from jira import JIRA
import pyodbc

# ---------------- CONFIGURATION ----------------
JIRA_URL = "https://your-domain.atlassian.net"
JIRA_EMAIL = "your-email@example.com"
JIRA_API_TOKEN = "your-api-token"
JIRA_PROJECT_KEY = "ABC"

SQL_SERVER = "your_sql_server"
SQL_DB = "your_database"
TABLE_NAME = "JiraReleaseDetails"

# ---------------- DATABASE CONNECTION ----------------
def get_connection():
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=" + SQL_SERVER + ";"
        "DATABASE=" + SQL_DB + ";"
        "Trusted_Connection=yes;"
    )
    return pyodbc.connect(conn_str)

def create_table_if_not_exists():
    query = f"""
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='{TABLE_NAME}' AND xtype='U')
    CREATE TABLE {TABLE_NAME} (
        jira_key NVARCHAR(100),
        assignee NVARCHAR(100),
        summary NVARCHAR(MAX),
        business_benefit NVARCHAR(MAX),
        release_component NVARCHAR(255),
        fix_version NVARCHAR(100)
    )
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    conn.close()

def save_to_db(df, version):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE fix_version = ?", version)
    for _, row in df.iterrows():
        cursor.execute(
            f"INSERT INTO {TABLE_NAME} VALUES (?, ?, ?, ?, ?, ?)",
            row['JIRA'], row['Assignee'], row['Summary'],
            row.get('Business Benefit', ''), row.get('Release Component', ''), version
        )
    conn.commit()
    conn.close()

def load_from_db(version):
    conn = get_connection()
    df = pd.read_sql(f"SELECT * FROM {TABLE_NAME} WHERE fix_version = ?", conn, params=[version])
    conn.close()
    return df

# ---------------- JIRA FUNCTIONS ----------------
@st.cache_data(ttl=300)
def get_jira_connection():
    options = {
        'server': JIRA_URL
    }
    return JIRA(options=options, basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN))

@st.cache_data(ttl=300)
def get_versions():
    jira = get_jira_connection()
    versions = jira.project_versions(JIRA_PROJECT_KEY)
    released = [v.name for v in versions if v.released]
    unreleased = [v.name for v in versions if not v.released]
    return released, unreleased

def get_issues_by_fix_version(version):
    jira = get_jira_connection()
    jql = f'project = {JIRA_PROJECT_KEY} AND fixVersion = "{version}"'
    issues = jira.search_issues(jql, maxResults=1000)
    data = []
    for issue in issues:
        data.append({
            "JIRA": issue.key,
            "Assignee": issue.fields.assignee.displayName if issue.fields.assignee else "",
            "Summary": issue.fields.summary,
            "Business Benefit": "",
            "Release Component": ""
        })
    return pd.DataFrame(data)

# ---------------- STREAMLIT UI ----------------
st.set_page_config(page_title="JIRA Release Tracker", layout="wide")
st.title("🚀 JIRA Release Dashboard")

create_table_if_not_exists()
released_versions, unreleased_versions = get_versions()

tab1, tab2 = st.tabs(["📦 Released", "🛠️ Unreleased"])

with tab1:
    selected_released = st.selectbox("Select Released Version", released_versions)
    if selected_released:
        existing_data = load_from_db(selected_released)
        if existing_data.empty:
            st.warning("No saved data found for this release.")
        st.data_editor(existing_data, key="released_df", num_rows="dynamic")

with tab2:
    selected_unreleased = st.selectbox("Select Unreleased Version", unreleased_versions)
    if selected_unreleased:
        df = get_issues_by_fix_version(selected_unreleased)
        editable_df = st.data_editor(df, key="unreleased_df", num_rows="dynamic")
        if st.button("💾 Save to SQL", use_container_width=True):
            save_to_db(editable_df, selected_unreleased)
            st.success("Data saved successfully!")
