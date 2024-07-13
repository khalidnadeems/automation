import streamlit as st
import pandas as pd

# Dummy data for environments, services, and their statuses
environments = ['Environment 1', 'Environment 2', 'Environment 3']
services_data = {
    'Environment 1': [
        {'Service Name': 'WinService1', 'Status': 'Stopped', 'Server': 'Server1'},
        {'Service Name': 'WinService2', 'Status': 'Running', 'Server': 'Server2'},
        {'Service Name': 'IISService1', 'Status': 'Disabled', 'Server': 'Server3'}
    ],
    'Environment 2': [
        {'Service Name': 'WinService3', 'Status': 'Running', 'Server': 'Server1'},
        {'Service Name': 'WinService4', 'Status': 'Stopped', 'Server': 'Server2'},
        {'Service Name': 'IISService2', 'Status': 'Running', 'Server': 'Server3'}
    ],
    'Environment 3': [
        {'Service Name': 'WinService5', 'Status': 'Running', 'Server': 'Server1'},
        {'Service Name': 'WinService6', 'Status': 'Disabled', 'Server': 'Server2'},
        {'Service Name': 'IISService3', 'Status': 'Stopped', 'Server': 'Server3'}
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

# Fetch services based on selected environment
services = services_data.get(selected_environment, [])

# Convert to dataframe
df_services = pd.DataFrame(services)

# Display dataframe with toggle buttons
st.write("Services in", selected_environment)

for idx, service in df_services.iterrows():
    col1, col2, col3, col4 = st.columns([3, 2, 2, 3])
    
    col1.write(service['Service Name'])
    col2.write(service['Status'])
    col3.write(service['Server'])
    
    if service['Status'] == 'Disabled':
        col4.write('Disabled')
    else:
        action = 'Stop' if service['Status'] == 'Running' else 'Start'
        if col4.button(action, key=idx):
            new_status = 'Stopped' if service['Status'] == 'Running' else 'Running'
            updated_service = update_service_status(service['Service Name'], new_status)
            if updated_service:
                st.success(f"{updated_service['Service Name']} is now {updated_service['Status']}")
            else:
                st.error("Failed to update service status")

# Refresh button
if st.button('Refresh'):
    st.experimental_rerun()
