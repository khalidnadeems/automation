import streamlit as st
import pandas as pd

# Dummy data for environments and their details
environments = ['Environment 1', 'Environment 2', 'Environment 3']
environment_details = {
    'Environment 1': [
        {'Server Name': 'Server1', 'Database Name': 'DB1', 'Owner': 'Owner1', 'Start Date': '2021-01-01', 'Finish Date': '2022-01-01'},
        {'Server Name': 'Server2', 'Database Name': 'DB2', 'Owner': 'Owner2', 'Start Date': '2021-02-01', 'Finish Date': '2022-02-01'},
    ],
    'Environment 2': [
        {'Server Name': 'Server3', 'Database Name': 'DB3', 'Owner': 'Owner3', 'Start Date': '2021-03-01', 'Finish Date': '2022-03-01'},
        {'Server Name': 'Server4', 'Database Name': 'DB4', 'Owner': 'Owner4', 'Start Date': '2021-04-01', 'Finish Date': '2022-04-01'},
    ],
    'Environment 3': [
        {'Server Name': 'Server5', 'Database Name': 'DB5', 'Owner': 'Owner5', 'Start Date': '2021-05-01', 'Finish Date': '2022-05-01'},
        {'Server Name': 'Server6', 'Database Name': 'DB6', 'Owner': 'Owner6', 'Start Date': '2021-06-01', 'Finish Date': '2022-06-01'},
    ]
}

# Dummy service data
services_data = {
    'Environment 1': [
        {'Service Name': 'WinService1', 'Status': 'Stopped', 'Server': 'Server1'},
        {'Service Name': 'WinService2', 'Status': 'Running', 'Server': 'Server2'},
    ],
    'Environment 2': [
        {'Service Name': 'WinService3', 'Status': 'Running', 'Server': 'Server3'},
        {'Service Name': 'WinService4', 'Status': 'Stopped', 'Server': 'Server4'},
    ],
    'Environment 3': [
        {'Service Name': 'WinService5', 'Status': 'Running', 'Server': 'Server5'},
        {'Service Name': 'WinService6', 'Status': 'Disabled', 'Server': 'Server6'},
    ]
}

# Function to update service status
def update_service_status(service_name, new_status):
    for service in services:
        if service['Service Name'] == service_name:
            service['Status'] = new_status
            return service
    return None

# Streamlit layout
st.title('Service Management Dashboard')

# Sidebar for environment selection
selected_environment = st.sidebar.selectbox("Select Environment", environments)

# Fetch environment details based on selected environment
environment_info = environment_details.get(selected_environment, [])
df_environment_info = pd.DataFrame(environment_info)

# Display environment details with checkboxes
st.write(f"Environment Details for {selected_environment}")
df_environment_info['Selected'] = False

for idx, row in df_environment_info.iterrows():
    df_environment_info.at[idx, 'Selected'] = st.checkbox(f"Select {row['Server Name']}", key=idx)

st.dataframe(df_environment_info)

# Fetch services based on selected environment
services = services_data.get(selected_environment, [])
df_services = pd.DataFrame(services)

# Display services with checkboxes
st.write(f"Services in {selected_environment}")
selected_services = []
for idx, service in df_services.iterrows():
    col1, col2, col3, col4 = st.columns([3, 2, 2, 3])
    
    selected = col1.checkbox(service['Service Name'], key=service['Service Name'])
    col2.write(service['Status'])
    col3.write(service['Server'])
    
    if selected:
        selected_services.append(service)

# Action buttons for selected services
if st.button('Start Selected Services'):
    for service in selected_services:
        if service['Status'] == 'Stopped':
            update_service_status(service['Service Name'], 'Running')
            st.success(f"Started {service['Service Name']}")

if st.button('Stop Selected Services'):
    for service in selected_services:
        if service['Status'] == 'Running':
            update_service_status(service['Service Name'], 'Stopped')
            st.success(f"Stopped {service['Service Name']}")

# Refresh button
if st.button('Refresh'):
    st.experimental_rerun()
