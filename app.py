import streamlit as st
import pandas as pd

# Dummy data for environments, Windows services, and IIS services
environments = ['Environment 1', 'Environment 2', 'Environment 3']
windows_services = {
    'Environment 1': ['WinService1', 'WinService2', 'WinService3'],
    'Environment 2': ['WinService4', 'WinService5', 'WinService6'],
    'Environment 3': ['WinService7', 'WinService8', 'WinService9']
}
iis_services = {
    'Environment 1': ['IISService1', 'IISService2', 'IISService3'],
    'Environment 2': ['IISService4', 'IISService5', 'IISService6'],
    'Environment 3': ['IISService7', 'IISService8', 'IISService9']
}

# Streamlit layout
st.title('Service Management Dashboard')

# Sidebar for environment selection
selected_environment = st.sidebar.selectbox("Select Environment", environments)

# Fetch services based on selected environment
win_services = windows_services.get(selected_environment, [])
iis_services = iis_services.get(selected_environment, [])

# Convert to dataframes
df_win_services = pd.DataFrame(win_services, columns=['Windows Services'])
df_iis_services = pd.DataFrame(iis_services, columns=['IIS Services'])

# Multi-select for services
selected_win_services = st.multiselect("Select Windows Services", df_win_services['Windows Services'], df_win_services['Windows Services'])
selected_iis_services = st.multiselect("Select IIS Services", df_iis_services['IIS Services'], df_iis_services['IIS Services'])

# Display dataframes
st.write("Selected Windows Services")
st.dataframe(df_win_services)
st.write("Selected IIS Services")
st.dataframe(df_iis_services)

# Action buttons
if st.button('Start Selected Services'):
    st.write(f"Starting services: {selected_win_services + selected_iis_services}")
    # Add your service start logic here

if st.button('Stop Selected Services'):
    st.write(f"Stopping services: {selected_win_services + selected_iis_services}")
    # Add your service stop logic here
