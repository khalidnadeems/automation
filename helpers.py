import pandas as pd
import pyodbc
from jira import JIRA

# --- DB CONFIGURATION ---
SERVER = 'your_sql_server'
DATABASE = 'your_database'
TABLE = 'JIRA_Release_Data'
DRIVER = 'ODBC Driver 17 for SQL Server'

# --- JIRA CONFIGURATION ---
JIRA_SERVER = 'https://your-jira-instance.atlassian.net'
JIRA_USER = 'your.email@example.com'
JIRA_API_TOKEN = 'your_api_token'
JIRA_PROJECT_KEY = 'PROJ'

# Connect to SQL Server using Windows Authentication
def get_connection():
    return pyodbc.connect(
        f"DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};Trusted_Connection=yes;"
    )

def create_table_if_not_exists():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            IF NOT EXISTS (
                SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{TABLE}'
            )
            CREATE TABLE {TABLE} (
                jira_key NVARCHAR(100),
                fix_version NVARCHAR(100),
                [Story Type] NVARCHAR(100),
                [User Sign-off Needed? Y/N] NVARCHAR(10),
                [Release Component] NVARCHAR(255),
                [Justification for Release] NVARCHAR(MAX),
                [Pre-Implementation Plan] NVARCHAR(MAX),
                [Implementation Plan] NVARCHAR(MAX),
                [Post Implementation Plan] NVARCHAR(MAX),
                [Risk / Impact if not released] NVARCHAR(MAX),
                [Rollback Plan] NVARCHAR(MAX),
                PRIMARY KEY (jira_key, fix_version)
            )
        """)
        conn.commit()

def get_versions():
    jira = JIRA(server=JIRA_SERVER, basic_auth=(JIRA_USER, JIRA_API_TOKEN))
    versions = jira.project(JIRA_PROJECT_KEY).versions
    released = sorted([v.name for v in versions if v.released], reverse=True)
    unreleased = sorted([v.name for v in versions if not v.released], reverse=True)
    return released, unreleased

def get_issues_by_fix_version(version):
    jira = JIRA(server=JIRA_SERVER, basic_auth=(JIRA_USER, JIRA_API_TOKEN))
    jql = f'project = {JIRA_PROJECT_KEY} AND fixVersion = "{version}" ORDER BY key ASC'
    issues = jira.search_issues(jql, maxResults=1000)

    data = []
    for issue in issues:
        fields = issue.fields
        data.append({
            "jira_key": issue.key,
            "Team Name": getattr(fields, "customfield_12345", "Team A"),  # Replace customfield_12345
            "JIRA": issue.key,
            "JIRA Type": fields.issuetype.name,
            "Assignee": fields.assignee.displayName if fields.assignee else "",
            "Summary": fields.summary,
            "Business Benefit": getattr(fields, "customfield_12346", ""),  # Replace customfield_12346
        })

    df = pd.DataFrame(data)
    df.columns = df.columns.str.strip()
    return df

def load_from_db(fix_version):
    try:
        with get_connection() as conn:
            query = f"SELECT * FROM {TABLE} WHERE fix_version = ?"
            df = pd.read_sql(query, conn, params=[fix_version])
            df.columns = df.columns.str.strip()
            return df
    except Exception as e:
        print("DB load failed:", e)
        return pd.DataFrame()

def save_to_db(df: pd.DataFrame, fix_version: str):
    df = df.copy()
    df.columns = df.columns.str.strip()
    df["fix_version"] = fix_version
    df["jira_key"] = df.get("jira_key", df.get("JIRA", ""))

    # Only keep expected DB columns
    expected_columns = [
        "jira_key", "fix_version", "Story Type",
        "User Sign-off Needed? Y/N", "Release Component",
        "Justification for Release", "Pre-Implementation Plan",
        "Implementation Plan", "Post Implementation Plan",
        "Risk / Impact if not released", "Rollback Plan"
    ]

    df = df[[col for col in expected_columns if col in df.columns]]

    with get_connection() as conn:
        cursor = conn.cursor()

        # Delete old entries for version
        cursor.execute(f"DELETE FROM {TABLE} WHERE fix_version = ?", fix_version)

        for _, row in df.iterrows():
            cursor.execute(f"""
                INSERT INTO {TABLE} (
                    jira_key, fix_version, [Story Type], [User Sign-off Needed? Y/N],
                    [Release Component], [Justification for Release], [Pre-Implementation Plan],
                    [Implementation Plan], [Post Implementation Plan],
                    [Risk / Impact if not released], [Rollback Plan]
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, tuple(row.get(col, "") for col in expected_columns))

        conn.commit()

def update_jira_fields(df: pd.DataFrame):
    jira = JIRA(server=JIRA_SERVER, basic_auth=(JIRA_USER, JIRA_API_TOKEN))

    for _, row in df.iterrows():
        try:
            issue = jira.issue(row["jira_key"])
            issue.update(fields={
                "summary": row.get("Summary", ""),
                "customfield_12346": row.get("Business Benefit", "")  # Replace with actual field ID
            })
        except Exception as e:
            print(f"Failed to update JIRA {row['jira_key']}: {e}")
