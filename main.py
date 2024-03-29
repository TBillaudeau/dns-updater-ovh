import streamlit as st
import ovh
import os
from dotenv import load_dotenv
import pandas as pd 
from collections import OrderedDict

load_dotenv()

#######################
#  OVH API endpoints  #
#######################

# https://eu.api.ovh.com/console-preview/?section=%2Fdomain&branch=v1#get-/domain/zone
# List all DNS of user
def list_dns_zones(client):
    endpoint = '/domain/zone'
    return client.get(endpoint)

# https://eu.api.ovh.com/console-preview/?section=%2Fdomain&branch=v1#get-/domain/zone/-zoneName-/record
# List DNS records of a domain
def get_dns_records(client, zoneName):
    endpoint = f'/domain/zone/{zoneName}/record'
    return client.get(endpoint)

# https://eu.api.ovh.com/console-preview/?section=%2Fdomain&branch=v1#get-/domain/zone/-zoneName-/record/-id-
# Get a DNS record object properties
def get_dns_record(client, zoneName, record_id):
    endpoint = f'/domain/zone/{zoneName}/record/{record_id}'
    record = client.get(endpoint)
    record = OrderedDict([(key, record[key]) for key in ['id', 'ttl', 'fieldType', 'subDomain', 'zone', 'target']])
    return record

# https://eu.api.ovh.com/console-preview/?section=%2Fdomain&branch=v1#delete-/domain/zone/-zoneName-/record/-id-
# Delete a DNS record object
def delete_dns_record(client, zoneName, record_id):
    endpoint = f'/domain/zone/{zoneName}/record/{record_id}'
    client.delete(endpoint)

# https://eu.api.ovh.com/console-preview/?section=%2Fdomain&branch=v1#put-/domain/zone/-zoneName-/record/-id-
# Update a DNS record
def update_dns_record(client, zoneName, subdomain, record_id, target, ttl=0):
    endpoint = f"/domain/zone/{zoneName}/record/{record_id}"
    data = {
        "subDomain": subdomain,
        "target": target,
        "ttl": ttl
    }
    client.put(endpoint, **data)
    
# https://eu.api.ovh.com/console-preview/?section=%2Fdomain&branch=v1#post-/domain/zone/-zoneName-/record
# Create a DNS record in a domain 
def create_dns_record(client, fieldType, subdomain, zoneName, target, ttl=0):
    endpoint = f"/domain/zone/{zoneName}/record"
    data = {
        "fieldType": fieldType,
        "subDomain": subdomain, #+"."+zoneName+"."
        "target": target,
        "ttl": ttl
    }
    client.post(endpoint, **data)



########################
#  Main Streamlit app  #
########################
def main():
    st.set_page_config(
        page_title="OVH DNS",
        page_icon="🌐",
        layout="wide",
        initial_sidebar_state="expanded",
    )   
    hide_st_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .st-emotion-cache-z5fcl4 {padding: 4rem 5rem 10rem;}
        </style>
        """
    st.markdown(hide_st_style, unsafe_allow_html=True)
    st.title(":blue[OVH] DNS Updater")
    st.sidebar.caption('Press R to refresh the page')
    st.sidebar.divider()

    # Get credentials from env
    ovh_endpoint = os.getenv('OVH_ENDPOINT')
    ovh_application_key = os.getenv('OVH_APPLICATION_KEY')
    ovh_application_secret = os.getenv('OVH_APPLICATION_SECRET')
    ovh_consumer_key = os.getenv('OVH_CONSUMER_KEY')

    # Authenticate with OVH API
    client = ovh.Client(
        endpoint=ovh_endpoint,
        application_key=ovh_application_key,
        application_secret=ovh_application_secret,
        consumer_key=ovh_consumer_key
    )

    # List all DNS zones of the user
    zones = list_dns_zones(client)
    selected_dns_zone = st.sidebar.selectbox('Select a DNS Zone', zones)
    st.sidebar.dataframe(pd.DataFrame(zones, columns=['DNS Zones']), hide_index=True, use_container_width=True)
    
    if selected_dns_zone:
        col1, col2 = st.columns([2,1])

        with col1:
            st.text('DNS Records')
            records = get_dns_records(client, selected_dns_zone)
            record_details = [get_dns_record(client, selected_dns_zone, record_id) for record_id in records][::-1]
            df = pd.DataFrame(record_details)
            df_placeholder = st.empty()  # Create a placeholder for the DataFrame
            df_placeholder.markdown(df.to_html(index=False), unsafe_allow_html=True)  # Display the DataFrame in the placeholder

        with col2:
            # st.text('Manage')
            tab1, tab2, tab3 = st.tabs(["Add", "Remove", "Update"])

            with tab1:
                record_types = ['CNAME', 'A', 'AAAA', 'NS', 'DNAME', 'TXT']
                fieldType = st.selectbox('Record Type', record_types)

                col3, col4 = st.columns(2)
                subdomain = col3.text_input('Sub-domain', key='create_subdomain')
                col4.text_input('Select a DNS Zone', selected_dns_zone, disabled=True)

                target = st.text_input('Target', key='create_target')
                if st.button('➕ Create Record'):
                    if subdomain not in df['subDomain'].values:
                        create_dns_record(client, fieldType, subdomain, selected_dns_zone, target)

                        # Update the DataFrame
                        records = get_dns_records(client, selected_dns_zone)
                        record_details = [get_dns_record(client, selected_dns_zone, record_id) for record_id in records][::-1]
                        df = pd.DataFrame(record_details)
                        df_placeholder.markdown(df.to_html(index=False), unsafe_allow_html=True)

                        # st.success(f'{fieldType} Record created successfully!')
                        st.toast(f'{fieldType} Record created successfully!', icon='✅')
                        # st.rerun()
                    else:
                        st.error('Subdomain already exists.')
                        st.toast('Subdomain already exists.', icon='❌')

            with tab2:
                delete_id = st.text_input('ID to Delete')
                if st.button('➖ Delete Record'):
                    if delete_id in str(df['id'].values):
                        delete_dns_record(client, selected_dns_zone, delete_id)

                        # Update the DataFrame
                        records = get_dns_records(client, selected_dns_zone)
                        record_details = [get_dns_record(client, selected_dns_zone, record_id) for record_id in records][::-1]
                        df = pd.DataFrame(record_details)
                        df_placeholder.markdown(df.to_html(index=False), unsafe_allow_html=True)

                        # st.success(f'{fieldType} Record deleted successfully!')
                        st.toast(f'{fieldType} Record deleted successfully!', icon='✅')
                        # st.rerun()
                    else:
                        st.error('ID not found.')
                        st.toast('ID not found.', icon='❌')

            with tab3:
                update_id = st.text_input('ID to Update')
                subdomain = st.text_input('Sub-domain', key='update_subdomain')
                target = st.text_input('Target', key='update_target')
                if st.button('🔄 Update Record'):
                    if update_id and subdomain and target:  # Check if inputs are not empty
                        update_dns_record(client, selected_dns_zone, subdomain, update_id, target)

                        # Update the DataFrame
                        records = get_dns_records(client, selected_dns_zone)
                        record_details = [get_dns_record(client, selected_dns_zone, record_id) for record_id in records][::-1]
                        df = pd.DataFrame(record_details)
                        df_placeholder.markdown(df.to_html(index=False), unsafe_allow_html=True)

                        # st.success(f'{fieldType} Record updated successfully!')
                        st.toast(f'{fieldType} Record updated successfully!', icon='✅')
                        # st.rerun()
                    else:
                        st.error('All fields must be filled in.')
                        st.toast('All fields must be filled in.', icon='❌')

if __name__ == "__main__":
    main()