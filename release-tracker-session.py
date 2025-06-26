import streamlit as st
import pandas as pd
import pyodbc
import requests
from jira import JIRA
from jira.resilientsession import ResilientSession

# —— CONFIGURATION ——
JIRA_URL = "https://your-domain.atlassian.net"
JIRA_EMAIL = "your-email@example.com"
JIRA_API_TOKEN = "your-api-token"
JIRA_PROJECT_KEY = "ABC"

SQL_SERVER = "your_sql_server"
SQL_DB = "your_database"
TABLE_NAME = "JiraReleaseDetails"

# —— PATCH missing max_retries on ResilientSession ——
# This ensures existing ResilientSession instances have the attribute
if not hasattr(ResilientSession, "max_retries"):
    ResilientSession.max_retries = 3

# —— DATABASE FUNCTIONS ——
def get_connection():
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={SQL_DB};"
        "Trusted_Connection=yes;"
    )
    return pyodbc.connect(conn_str)

def create_table_if_not_exists():
    q = f"""
    IF NOT EXISTS (
      SELECT * FROM sysobjects
      WHERE name='{TABLE_NAME}' AND xtype='U'
    )
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
    conn.execute(q)
    conn.commit()
    conn.close()

def save_to_db(df, version):
    conn = get_connection()
    conn.execute(f"DELETE FROM {TABLE_NAME} WHERE fix_version = ?", version)
    for _, r in df.iterrows():
        conn.execute(
            f"INSERT INTO {TABLE_NAME} VALUES (?, ?, ?, ?, ?, ?)",
            r['JIRA'], r['Assignee'], r['Summary'],
            r.get('Business Benefit', ''), r.get('Release Component', ''), version
        )
    conn.commit()
    conn.close()

def load_from_db(version):
    conn = get_connection()
    df = pd.read_sql(
        f"SELECT * FROM {TABLE_NAME} WHERE fix_version = ?",
        conn, params=[version]
    )
    conn.close()
    return df

# —— JIRA FUNCTIONS ——
@st.cache_data(ttl=300)
def get_jira_connection():
    options = {'server': JIRA_URL}
    return JIRA(options=options, basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN))

@st.cache_data(ttl=300)
def get_versions():
    jira = get_jira_connection()
    vs = jira.project_versions(JIRA_PROJECT_KEY)
    return (
        [v.name for v in vs if v.released],
        [v.name for v in vs if not v.released]
    )

def get_issues_by_fix_version(version):
    jira = get_jira_connection()
    issues = jira.search_issues(
        f'project={JIRA_PROJECT_KEY} AND fixVersion="{version}"',
        maxResults=1000
    )
    rows = []
    for i in issues:
        rows.append({
            "JIRA": i.key,
            "Assignee": i.fields.assignee.displayName if i.fields.assignee else "",
            "Summary": i.fields.summary,
            "Business Benefit": "",
            "Release Component": ""
        })
    return pd.DataFrame(rows)

# —— STREAMLIT UI ——
st.set_page_config(page_title="JIRA Release Tracker", layout="wide")
st.title("🚀 JIRA Release Dashboard")

create_table_if_not_exists()
released, unreleased = get_versions()

tab1, tab2 = st.tabs(["📦 Released", "🛠️ Unreleased"])

with tab1:
    sel = st.selectbox("Select Released Version", released)
    if sel:
        df0 = load_from_db(sel)
        if df0.empty:
            st.warning("No saved data found for this release.")
        st.data_editor(df0, key="released_df", num_rows="dynamic")

with tab2:
    sel2 = st.selectbox("Select Unreleased Version", unreleased)
    if sel2:
        df1 = get_issues_by_fix_version(sel2)
        ed = st.data_editor(df1, key="unreleased_df", num_rows="dynamic")
        if st.button("💾 Save to SQL"):
            save_to_db(ed, sel2)
            st.success("Data saved successfully!")
