import logging

from zoomus import ZoomClient
import json
import csv
import chardet


logger = logging.getLogger(__name__)

def get_user_id(user_email):
    """
    Get the member id based on the user email.
    """
    client = init_zoom_client()
    user_response = client.user.list()
    user_data = json.loads(user_response.content)
    
    for user in user_data['users']:
        logging.debug(user['email'])
        if user['email'] == user_email.lower():
            logging.debug("user id is : " + user['id'])
            return user['id']
        
    if user_data['next_page_token'] is not None:
        user_response = client.user.list(**{'page_token': user_data['next_page_token']})
        user_data = json.loads(user_response.content)
        for user in user_data['users']:
            logging.debug(user['email'])
            if user['email'] == user_email.lower():
                logging.debug("user id is : " + user['id'])
                return user['id']



def init_zoom_client(zoomclientId, zoomclientSecret, zoomaccountId):
    """
    Initialize Zoom client using session data.
    """
    
    zoomcId = zoomclientId
    zoomcSecret = zoomclientSecret
    zoomacId = zoomaccountId
    
    client = ZoomClient(zoomcId, zoomcSecret, zoomacId)
    logging.debug("client created")
    return client

def defaut_site_id():
    """
    Retrieve the default site id.
    """
    client = init_zoom_client()
    call_queues_response = client.phone.call_queues()

    call_queues = json.loads(call_queues_response.content)
    for queue in call_queues['call_queues']:
        logging.debug(queue)
        if queue['site']['name'] == 'Main Site':
            logging.debug("Main Site ID is: " + queue['id'])
            return queue['site']['id']

def site_id(s_name , client): 
    #client = init_zoom_client()
    sites_response = client.phone.site_list(**{'page_size': 300})
    logging.debug("site name searching for "+s_name)
    sites = json.loads(sites_response.content)
    for site in sites['sites']:
        logging.debug("site name "+site['name'])
        if site['name'] == s_name:
            logging.debug("Site ID is: " + site['id'])
            return site['id']

def call_queue_id(extension_id, client):
    """
    Get the call queue id based on the call queue name.
    """
    #client = init_zoom_client()
    call_queues_response = client.phone.call_queues()
    call_queues = json.loads(call_queues_response.content)
    for queue in call_queues['call_queues']:
        if queue['extension_number'] == int(extension_id):
            logging.debug("call queue id is : " + queue['id'])
            return queue['id']

def cc_queue_id1(queue_name):
    """
    Get the contact center queue id based on the queue name.
    """
    client = init_zoom_client()
    call_queues_response = client.contact_center.queues_list()

    call_queues = json.loads(call_queues_response.content)
    if 'queues' not in call_queues:
        return None

    for queue in call_queues['queues']:
        logging.debug(queue)
        if queue['queue_name'] == queue_name:
            logging.debug("CC queue id is : " + queue['queue_id'])
            return queue['queue_id']

def common_area_extension_id(name, client):
    #client = init_zoom_client()
    ca_response = client.phone.common_area_extension_id(**{'page_size' : '100'})
    ca_data = json.loads(ca_response.content)

    while True:
        for ca in ca_data['common_areas']:
            logging.debug(ca)
            logging.debug("ca name {}".format(ca['display_name']))
            logging.debug("common area extension to match {}".format(name))
            if ca['display_name'] == name:
                logging.debug("common area extension id is : " + ca['id'])
                return ca['id']

        # Check if there's a next page
        if 'next_page_token' in ca_data and ca_data['next_page_token']:
            # If there's a next page, get the next page of common area extensions
            logging.debug("Getting next page of common area extensions")
            logging.debug("next page token {}".format(ca_data['next_page_token']))
            ca_response = client.phone.common_area_extension_id(**{'page_size' : '100', 'next_page_token': ca_data['next_page_token']})
            ca_data = json.loads(ca_response.content)
        else:
            # If there's no next page, break the loop
            logging.debug("No next page of common area extensions")
            break

    return None

def business_hours_id(bh_name):
    """
    Get the business hours id based on the business hours name.
    """
    client = init_zoom_client()
    bhs_response = client.contact_center.business_hours()

    bhs_data = json.loads(bhs_response.content)
    for bhs in bhs_data['business_hours']:
        logging.debug(bhs)
        if bhs['business_hour_name'] == bh_name:
            logging.debug("business hours id is : " + bhs['business_hour_id'])
            return bhs['business_hour_id']
        
def disposition_set_id(ds_name):
    """
    Get the disposition set id based on the disposition set name.
    """
    client = init_zoom_client()
    ds_response = client.contact_center.dispositions_set_list()

    ds_data = json.loads(ds_response.content)
    for ds in ds_data['disposition_sets']:
        logging.debug(ds)
        if ds['disposition_set_name'] == ds_name:
            logging.debug("disposition set id is : " + ds['disposition_set_id'])
            return ds['disposition_set_id']

def disposition_id(d_name):
    """
    Get the disposition id based on the disposition name.
    """
    client = init_zoom_client()
    d_response = client.contact_center.dispositions_list()

    d_data = json.loads(d_response.content)
    for d in d_data['dispositions']:
        logging.debug(d)
        if d['disposition_name'] == d_name:
            logging.debug("disposition id is : " + d['disposition_id'])
            return d['disposition_id']

def get_role_id(role_name, client):
    """
    Get the role id based on the client.
    """
    #client = init_zoom_client()
    role_response = client.contact_center.get_request("/contact_center/roles") 
    #logger.info(role_response.content)
    role_data = json.loads(role_response.content)
    for role in role_data['roles']:
        logging.debug(role)
        if role['role_name'] == role_name:
            logging.debug("role id is : " + role['role_id'])
            return role['role_id']

def member_id(user_email):
    """
    Get the member id based on the user email.
    """
    client = init_zoom_client()
    user_response = client.phone.users()
    user_data = json.loads(user_response.content)
    for user in user_data['users']:
        logging.debug(user)
        if user['email'] == user_email:
            logging.debug("user id is : " + user['id'])
            return user['id']
        
def process_csv(request, zoomclientId, zoomclientSecret, zoomaccountId, output, action_success):
    """
    Process the CSV file and return the reader object.
    Use this method when there is no dictionary required in the parameters
    """
    file = request.files['csv_file']
    if file.filename == '':
        logger.info("No file selected")
        output.append("No file selected")
        
    filename = file.filename if file.filename else "Unnamed file"
    # Log the customer action
    logger.info(f"CSV file {filename} uploaded successfully")
    # Process the CSV file here
    csv_data = file.stream.read().decode('utf-8')
    reader = csv.reader(csv_data.splitlines()) 
    next(reader)
    return reader

def process_csv_dict(request, zoomclientId, zoomclientSecret, zoomaccountId, output, action_success):
    """
    Process the CSV file and return the reader object.
    Use this method when there is a dictionary required in the parameters. 
    Uses DictReader instead of reader to handle (but this can mess up non-dictionary calls -
    hence the separate method)
    """
    file = request.files['csv_file']
    if file.filename == '':
        logger.info("No file selected")
        output.append("No file selected")
        
    filename = file.filename if file.filename else "Unnamed file"
    # Log the customer action
    logger.info(f"CSV file {filename} uploaded successfully")
    # Process the CSV file here
    csv_data = file.stream.read().decode('utf-8')
    reader = csv.DictReader(csv_data.splitlines()) 
    return reader

def validate_zoom_token():
    try:
            client = init_zoom_client()
            client_request = client.user.me()
            print(client_request.status_code)

    except Exception as e:
            print(e)
            return False
    if client_request.status_code == 400 or client_request.status_code == 200:
            return True
    else:
            return False
    
def flow_id(f_name):
    client = init_zoom_client()
   
    f_response = client.contact_center.flows_list(**{'page_size': 300})

    f_data = json.loads(f_response.content)
    if 'flows' not in f_data:
        return None
    for f in f_data['flows']:
        logging.debug("flow name "+f['flow_name'])
        if f['flow_name'] == f_name:
            logging.debug("flow id is : " + f['flow_id'])
            return f['flow_id']
    return None
def inbox_id(inbox_name):
    client = init_zoom_client()
    inbox_response = client.contact_center.inbox_list()

    inbox_data = json.loads(inbox_response.content)
    for inbox in inbox_data['inboxes']:
        logging.debug(inbox)
        if inbox['inbox_name'] == inbox_name:
            logging.debug("inbox id is : " + inbox['inbox_id'])
            return inbox['inbox_id']
    return None

def cc_queue_id(queue_name, client):
    params = {'page_size': 300}
    call_queues_response = client.contact_center.queues_list(**params)

    call_queues = json.loads(call_queues_response.content)
    for queue in call_queues['queues']:
        logging.debug(queue)
        if queue['queue_name'] == queue_name:
            logging.debug("CC queue id is : " + queue['queue_id'])
            return queue['queue_id']

def site_json(row):
    default_emergency_address = {
                "country": row.get("country"),
                "address_line1": row.get("address_line1"),
                "city": row.get("city"),
                "zip": row.get("zip"),
                "state_code": row.get("state_code"),
                "address_line2": row.get("address_line2")
            }

            # Create the short_extension dictionary
    short_extension = {
                "length": int(row.get("short_extension_length")) if row.get("short_extension_length") else None
            }

            # Create the main dictionary
    data = {
                "name": row.get("name"),
                "auto_receptionist_name": row.get("auto_receptionist_name"),
                "default_emergency_address": default_emergency_address,
                "short_extension": short_extension,
                "site_code": int(row.get("site_code")) if row.get("site_code") else None
            }
    return data

def check_utf8(file):
    raw_data = file.stream.read()
    result = chardet.detect(raw_data)
    file_encoding = result['encoding']
    return file_encoding.lower() in ('utf-8', 'ascii')

def auto_receptionist_id(ar_name, client):
    ar_response = client.phone.get_request("/phone/auto_receptionists")
    ar_data = json.loads(ar_response.content)

    while True:
        for ar in ar_data['auto_receptionists']:
            logging.debug(ar)
            if ar['name'] == ar_name:
                logging.debug("auto receptionist id is : " + ar['id'])
                return ar['id']

        # Check if there's a next page
        if 'next_page_token' in ar_data and ar_data['next_page_token']:
            # If there's a next page, get the next page of auto receptionists
            ar_response = client.phone.get_request("/phone/auto_receptionists", params={'next_page_token': ar_data['next_page_token']})
            ar_data = json.loads(ar_response.content)
        else:
            # If there's no next page, break the loop
            break

    return None

def validate_emergency_csv(file):

    reader = csv.reader(codecs.getreader("utf-8")(file.stream))

    headers = next(reader)
    if headers != ['name', 'emails', 'target_name']:
        return "Invalid headers in CSV file."

    

    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    for row in reader:
        if len(row) != 3:
            return "Invalid number of columns in a row."
        if not isinstance(row[0], str) or not isinstance(row[2], str):
            return "Invalid data type in columns."
        emails = row[1].split(';')
        for email in emails:
            email = email.strip()  # Remove leading/trailing whitespace
            if not re.fullmatch(email_regex, email):
                return f"Invalid email address: {email}"

    return None