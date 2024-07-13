import streamlit as st
import pandas as pd

# Dummy data for environments, services, and their statuses
environments = ['Environment 1', 'Environment 2', 'Environment 3']
services_data = {
    'Environment 1': [
        {'Service Name': 'WinService1', 'Status': 'Stopped', 'Server': 'Server1'},
        {'Service Name': 'WinService2', 'Status': 'Running', 'Server': 'Server2'},
        {'Service Name': 'IISService1', 'Status': 'Disabled', 'Server': 'Server3'},
        # Add more services as needed
    ],
    'Environment 2': [
        {'Service Name': 'WinService3', 'Status': 'Running', 'Server': 'Server1'},
        {'Service Name': 'WinService4', 'Status': 'Stopped', 'Server': 'Server2'},
        {'Service Name': 'IISService2', 'Status': 'Running', 'Server': 'Server3'},
        # Add more services as needed
    ],
    'Environment 3': [
        {'Service Name': 'WinService5', 'Status': 'Running', 'Server': 'Server1'},
        {'Service Name': 'WinService6', 'Status': 'Disabled', 'Server': 'Server2'},
        {'Service Name': 'IISService3', 'Status': 'Stopped', 'Server': 'Server3'},
        # Add more services as needed
    ]
}

# Function to update service status
def update_service_status(service_name, new_status):
    for service in services:
        if service['Service Name'] == service_name:
            service['Status'] = new_status
            return service
    return None

# Pagination functions
def get_paginated_data(data, page, page_size):
    start_index = page * page_size
    end_index = start_index + page_size
    return data[start_index:end_index]

# Streamlit layout
st.title('Service Management Dashboard')

# Sidebar for environment selection
selected_environment = st.sidebar.selectbox("Select Environment", environments)

# Fetch services based on selected environment
services = services_data.get(selected_environment, [])

# Convert to dataframe
df_services = pd.DataFrame(services)

# Pagination controls
page_size = 5
total_pages = len(df_services) // page_size + (1 if len(df_services) % page_size > 0 else 0)
page_number = st.sidebar.number_input("Page", min_value=0, max_value=total_pages-1, value=0)

# Display paginated dataframe
paginated_services = get_paginated_data(df_services, page_number, page_size)
st.write(f"Services in {selected_environment} - Page {page_number+1} of {total_pages}")

for idx, service in paginated_services.iterrows():
    col1, col2, col3, col4 = st.columns([3, 2, 2, 3])
    
    col1.write(service['Service Name'])
    col2.write(service['Status'])
    col3.write(service['Server'])
    
    if service['Status'] == 'Disabled':
        col4.write('Disabled')
    else:
        action = 'Stop' if service['Status'] == 'Running' else 'Start'
        if col4.button(action, key=f"{idx}-{page_number}"):
            new_status = 'Stopped' if service['Status'] == 'Running' else 'Running'
            updated_service = update_service_status(service['Service Name'], new_status)
            if updated_service:
                st.success(f"{updated_service['Service Name']} is now {updated_service['Status']}")
            else:
                st.error("Failed to update service status")

# Refresh button
if st.button('Refresh'):
    st.experimental_rerun()

# Navigation buttons
col1, col2, col3 = st.columns([1, 1, 1])
if col1.button('Previous'):
    if page_number > 0:
        page_number -= 1
        st.experimental_rerun()
if col3.button('Next'):
    if page_number < total_pages - 1:
        page_number += 1
        st.experimental_rerun()
