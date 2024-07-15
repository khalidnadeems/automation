import streamlit as st
import pandas as pd

# Define the servers for each environment
ENV_SERVERS = {
    "Development": ["dev-server1", "dev-server2"],
    "Testing": ["test-server1", "test-server2"],
    "Production": ["prod-server1", "prod-server2"]
}

# Sample function implementations (replace with real implementations)
def fetch_services(servers, username, password):
    # Dummy data for example purposes
    windows_services = pd.DataFrame({
        'Name': ['Service1', 'Service2', 'Service3'],
        'Status': ['Running', 'Stopped', 'Running'],
        'DisplayName': ['Service One', 'Service Two', 'Service Three'],
        'server': ['Server1', 'Server2', 'Server1']
    })
    iis_services = pd.DataFrame({
        'Name': ['Site1', 'Site2', 'Site3'],
        'State': ['Started', 'Stopped', 'Started'],
        'server': ['Server1', 'Server2', 'Server1']
    })
    return windows_services, iis_services

def manage_service(server, username, password, service_name, action):
    # Dummy implementation
    print(f"{action} service {service_name} on {server}")
    return True

def main():
    st.set_page_config(layout="wide")
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
            st.session_state.windows_df = windows_df
            st.session_state.iis_df = iis_df

    if 'windows_df' in st.session_state and 'iis_df' in st.session_state:
        windows_df = st.session_state.windows_df
        iis_df = st.session_state.iis_df

        st.subheader("Windows Services")
        windows_df['select'] = [False] * len(windows_df)
        for index, row in windows_df.iterrows():
            windows_df.at[index, 'select'] = st.checkbox(f"Select {row['Name']} on {row['server']}", key=f"windows_{index}")

        st.subheader("IIS Services")
        iis_df['select'] = [False] * len(iis_df)
        for index, row in iis_df.iterrows():
            iis_df.at[index, 'select'] = st.checkbox(f"Select {row['Name']} on {row['server']}", key=f"iis_{index}")

        selected_windows_services = windows_df[windows_df['select']]
        selected_iis_services = iis_df[iis_df['select']]

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

if __name__ == "__main__":
    main()
