import streamlit as st

# Define the servers for each environment
ENV_SERVERS = {
    "Development": ["dev-server1", "dev-server2"],
    "Testing": ["test-server1", "test-server2"],
    "Production": ["prod-server1", "prod-server2"]
}

def fetch_services(servers, username, password):
    all_windows_services = pd.DataFrame()
    all_iis_services = pd.DataFrame()
    
    for server in servers:
        try:
            windows_services = get_remote_windows_services(server, username, password)
            iis_services = get_remote_iis_services(server, username, password)
            
            all_windows_services = pd.concat([all_windows_services, windows_services], ignore_index=True)
            all_iis_services = pd.concat([all_iis_services, iis_services], ignore_index=True)
        except Exception as e:
            st.error(f"Failed to fetch services from {server}: {e}")
    
    return all_windows_services, all_iis_services

st.title("Service Management Dashboard")

environment = st.selectbox("Select Environment", ["Development", "Testing", "Production"])
servers = ENV_SERVERS.get(environment, [])
username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Fetch Services"):
    if not servers:
        st.error("No servers defined for the selected environment.")
    else:
        windows_df, iis_df = fetch_services(servers, username, password)
        
        st.subheader("Windows Services")
        windows_df['select'] = False
        windows_services = st.data_editor(windows_df, use_container_width=True, key='windows_services')
        
        st.subheader("IIS Services")
        iis_df['select'] = False
        iis_services = st.data_editor(iis_df, use_container_width=True, key='iis_services')
        
        selected_windows_services = windows_services[windows_services['select']]
        selected_iis_services = iis_services[iis_services['select']]
        
        if st.button("Start Selected Services"):
            for idx, service in selected_windows_services.iterrows():
                manage_service(service['server'], username, password, service['Name'], 'Start')
            for idx, service in selected_iis_services.iterrows():
                manage_service(service['server'], username, password, service['Name'], 'Start')
            st.success("Selected services started.")
        
        if st.button("Stop Selected Services"):
            for idx, service in selected_windows_services.iterrows():
                manage_service(service['server'], username, password, service['Name'], 'Stop')
            for idx, service in selected_iis_services.iterrows():
                manage_service(service['server'], username, password, service['Name'], 'Stop')
            st.success("Selected services stopped.")
