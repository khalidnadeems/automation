
-- JiraReleaseDetails table creation
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='JiraReleaseDetails' AND xtype='U')
CREATE TABLE JiraReleaseDetails (
    team_name NVARCHAR(100),
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
);
