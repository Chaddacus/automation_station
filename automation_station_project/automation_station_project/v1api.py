
import requests
import json

from requests import Request

from .helpers import common_area_extension_id

import logging 

logger = logging.getLogger(__name__)

#https://us01cci.zoom.us/v1/queues/query?page=1&size=15


def get_site_id(bearer_token, org_account_info, site_name):
    base_url = f"https://us01pbx.zoom.us/api/v2/pbx/account/{org_account_info}/site-module?module=siteOther&operate=Edit&page_size=100"
    headers = { "Authorization": "Bearer " + bearer_token }
    
    page_number = 1
    total_pages = None

    while True:
        url = f"{base_url}&page_number={page_number}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Received non-200 response: {response.status_code}")  # Debugging line
            return None

        data = response.json()
        sites = data.get("records", [])

        for site in sites:
            if site.get("name") == site_name:
                return site.get("siteId")

        if total_pages is None:
            total_pages = data.get("pageTotal", 0)
            print(f"Total pages found: {total_pages}")  # Debugging line

        if page_number >= total_pages:
            print(f"Reached end of pages at page {page_number}")  # Debugging line
            break

        page_number += 1

    return None


def add_alert_rule(bearer_token, org_account_info, payload):
    url = f"https://us01pbx.zoom.us/api/v2/pbx/account/{org_account_info}/alert/4"

    headers = {
        "Authorization": "Bearer " + bearer_token,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=payload)

    return response

def get_alerts(bearer_token, org_account_info):
    url = f"https://us01pbx.zoom.us/api/v2/pbx/account/{org_account_info}/alert?page_number=1&page_size=15&isLimit=true"
    headers = { "Authorization": "Bearer " + bearer_token }
    
    all_alerts = []
    page_number = 1
    total_pages = None
    
    while True:
        print(f"Fetching page {page_number}")  # Debugging line
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Received non-200 response: {response.status_code}")  # Debugging line
            return response.json()

        data = response.json()
        alerts = data.get("records", [])
        all_alerts.extend(alerts)

        print(f"Found {len(alerts)} alerts on page {page_number}")  # Debugging line

        if total_pages is None:
            total_pages = data.get("pageTotal", 0)
            print(f"Total pages found: {total_pages}")  # Debugging line

        if page_number >= total_pages:
            print(f"Reached end of pages at page {page_number}")  # Debugging line
            break

        page_number += 1
        url = f"https://us01pbx.zoom.us/api/v2/pbx/account/{org_account_info}/alert?page_number={page_number}&page_size=15&isLimit=true"

    print(f"Found a total of {len(all_alerts)} alerts")  # Debugging line
    return all_alerts


def change_ivr_menu(bearer_token, org_account_info, extension_id, ivr_id, payload):
    url = f"https://us01pbx.zoom.us/api/v2/pbx/account/{org_account_info}/extension/{extension_id}/ivr/{ivr_id}"
    headers = {"Authorization": "Bearer " + bearer_token}
    
    response = requests.patch(url, headers=headers, json=payload)
    
    return response.json()

def get_ivr_data_list(bearer_token, org_account_info, extension_id):
    url = f"https://us01pbx.zoom.us/api/v2/pbx/account/{org_account_info}/extension/{extension_id}/ivr"
    headers = { "Authorization": "Bearer " + bearer_token}
    response = requests.get(url, headers=headers)
    ivrid_list = []
    if response.status_code == 200:
        data = response.json()
        for record in data:
            if record.get("ivrId"):
                ivrid_list.append(record.get("ivrId"))
        return ivrid_list
    elif response.status_code == 401:
        return "Unauthorized"

    return "Error fetching extension id"

def get_auto_receptionist_id(bearer_token, org_account_info, auto_receptionist_extension):
    logger.debug(f"Getting auto receptionist id for extension {auto_receptionist_extension}")
    logger.debug(f"org_account_info: {org_account_info}")
    
    records = list_auto_receptionists_ext(bearer_token, org_account_info)
    
    for record in records:
        #print(auto_receptionist_extension)
        #print (record)

        if record.get("extensionNumber") == int(auto_receptionist_extension):
            #print ("output is: ", record.get("extensionId"))
            return record.get("extensionId")
    return None

def get_external_extension_id(bearer_token, org_account_info, phone_number):
    page_number = 1
    while True:
        url = f"https://us01pbx.zoom.us/api/v2/pbx/account/{org_account_info}/callHandling/byop/external-extension?page_number={page_number}&level=&keyword=&source=AR"
        headers = { "Authorization": "Bearer " + bearer_token}

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return response.json()

        data = response.json()
        records = data.get("records", [])
        
        if not records:
            return None
        
        for record in records:
            
            phone_numbers = record.get("phoneNumberList", [])

            if not phone_numbers:
                return None
            
            for num in phone_numbers:
                                
                if phone_number.strip() in num.strip():
                    print ("match found")
                    external_ext_id = record.get("externalExtensionId")
                    return external_ext_id
                   

        # Check if there are more pages
        if page_number >= data.get("pageTotal", 0):
            print(f"Reached end of pages at page {page_number}")
            break

        # Increment the page number for the next iteration
        page_number += 1

        return None

def list_auto_receptionists_ext(bearer_token, org_account_info):
    url = f'https://us01pbx.zoom.us/api/v2/pbx/account/{org_account_info}/auto-receptionist?page_number=1&page_size=15&isLimit=true'
    headers = { "Authorization": "Bearer " + bearer_token }

    all_records = []
    page_number = 1
    total_pages = None

    while True:
        #print(f"Fetching page {page_number}")  # Debugging line
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            logger.debug(f"Received non-200 response: {response.status_code}")  # Debugging line
            return response.json()

        data = response.json()
        records = data.get("records", [])
        all_records.extend(records)

        #print(f"Found {len(records)} records on page {page_number}")  # Debugging line

        if total_pages is None:
            total_pages = data.get("pageTotal", 0)
            #f"Total pages found: {total_pages}")  # Debugging line

        if page_number >= total_pages:
            logger.debug(f"Reached end of pages at page {page_number}")  # Debugging line
            break

        page_number += 1
        url = f'https://us01pbx.zoom.us/api/v2/pbx/account/{org_account_info}/auto-receptionist?page_number={page_number}&page_size=15&isLimitRole=true'

    logger.debug(f"Found a total of {len(all_records)} records")  # Debugging line
    return all_records

def extract_ivr_resource_id(bearer_token, org_account_info, ivr_extension_id, level,extension_number,):
    url = f"https://us01pbx.zoom.us/api/v2/pbx/account/{org_account_info}/callHandling/extension/{ivr_extension_id}/s?level={level}&keyword={extension_number}&source=AR"
    headers = {"Authorization": "Bearer " + bearer_token}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        
        callqueue_id = None
        if isinstance(data, list):
            print(f"resource instance check ok level is {level}")
            for record in data:
                #if isinstance(record, dict) and record.get('displayName') == "(Ryan) EA Call Queue":
                print(record.get('extensionNumber'))
                if isinstance(record, dict) and record.get('extensionNumber') == extension_number:
                    #print("record id Match found")
                     
                    callqueue_id = record.get('extensionId')
                    

        return callqueue_id

def translate_row(row, bearer_token,  org_account_info , ivr_extension_id):
    
    action_mapping = {
        ('fwd', 'ar'): '7',
        ('vm', 'ar'): '100',
        ('fwd', 'user'): '3',
        ('vm', 'user'): '200',
        ('fwd', 'call_queue'): '4',
        ('vm', 'call_queue'): '400',
        ('fwd', 'com_area'): '10',
        ('fwd', 'ext'): '26',
    }

    # Check if all 'action' and 'extension_type' fields are empty
    if all(row.get(f'action_{i}') == '' and row.get(f'extension_type_{i}') == '' for i in range(13)):
        return []  # Return an empty list if all fields are empty

    payloads = []  # List to store the codes

    for i in range(13):  # Assuming the numbers go from 0 to 12
        
        action_key = f'action_{i}'
        extension_type_key = f'extension_type_{i}'
        extension = f'extension_{i}'

        action = row.get(action_key)
        extension_type = row.get(extension_type_key)

        extension_num = row.get(extension)

        logger.debug(f"!!!! Digit {i} , {action_key}: {action}, {extension_type_key}: {extension_type}, {extension} {extension_num}")
        id = None 
        #Level of ivr information
        #level=1, extension
        #level=2, call queue
        #level=3, auto receptionist
        #level=4, Common Area
        #level=5, Site
        #level=6, Empty ??
        if action is None or extension_type is None or action == '' or extension_type == '':
            #print("Skipping")
            continue  # Skip this iteration if either 'action' or 'extension_type' is empty
        
        if extension_type == 'ar':
            level = 3
           
            id = extract_ivr_resource_id(bearer_token, org_account_info, ivr_extension_id, level, extension_num)
           
            

        if extension_type == 'user':
            level = 1
            #user_id = row.get(f'extension_{i}')
            id = extract_ivr_resource_id(bearer_token, org_account_info, ivr_extension_id, level, extension_num)

        if extension_type == 'call_queue':
            level = 2
            #call_queue_id = row.get(f'extension_{i}')
            id = extract_ivr_resource_id(bearer_token, org_account_info, ivr_extension_id, level, extension_num)
           
            

        if extension_type == 'com_area':
            level = 4
            id = extract_ivr_resource_id(bearer_token, org_account_info, ivr_extension_id, level, extension_num)
            
        
        if extension_type == 'ext':
            print("external extension")
            print(extension_num)
            
            id = get_external_extension_id(bearer_token, org_account_info, extension_num)
            
        
        if id is None and extension_num != '0':
            error_message = f"Resource with extension '{extension_num}' not found at index {i}"
            return '0',[error_message]
        
        #if str(extension_num) == '0':


        digit = i
        
        if i == 10:
            digit = "*"
        if i == 11:
            digit = "#"
        
        code = action_mapping.get((action, extension_type))

              
        if code is None and extension_num != '0':
            error_message = f"Invalid action '{action}' or extension '{extension_num}' at index {i}"
            return '0',[error_message]  # Return None if an invalid action or extension type is found

        payload = {
        
        "digit": str(digit),
        "openHourAction": int(code),
        "openHourArgs" : id,
        "openHourPromptWait":3,
        "openHourVoice":"",
        "openHourVoiceSynonyms":"",
        "openHourPromptRepeat":3,
        "openHourSubArgs":"",
        }
        
        
        

        if code == '200' or code == '400' or code == '100':

            payload['openVoicemailType'] = code
            payload['openHourAction'] = 0

        if str(extension_num) == '0':
            payload = {
        
        "digit": str(digit),
        "openHourAction": int(-1),
        "openHourArgs" : "",
        "openHourPromptWait":3,
        "openHourVoice":"",
        "openHourVoiceSynonyms":"",
        "openHourPromptRepeat":3,
        "openHourSubArgs":"",
        }

        payloads.append(payload)

    
    
    

    return row.get("ar_extension"), payloads  # Return the list of codes

def api_pbx_account_info(bearer_token):
    url = "https://us01pbx.zoom.us/api/v2/pbx/current/account"

    headers = {
            "Authorization": "Bearer {}".format(bearer_token)
        }

    logger.debug("zoom v1 api pbx token {}".format(bearer_token))

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
            
        #logger.debug("queue information: {}".format(response.json()))
        return response.json()
     
    elif response.status_code == 401:
        logger.debug("Failed to retrieve v1 queue information Token is not valid. Status code: {}".format( response.status_code))
        return None        
    else:
        logger.debug("Failed to retrieve v1 queue information. Status code: {}".format( response.status_code))
        
        return None
    
def api_pbx_group_detail(bearer_token, account_id, group_id):
    url = f"https://us01pbx.zoom.us/api/v2/pbx/account/{account_id}/group/{group_id}"

    headers = {
            "Authorization": "Bearer {}".format(bearer_token)
        }

    logger.debug("zoom v1 api pbx token {}".format(bearer_token))

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
                
            #logger.debug("group information: {}".format(response.json()))
            return response.json()
    else:
            logger.debug("Failed to retrieve v1 group information. Status code: {}".format( response.status_code))
            return None



def api_pbx_call_queue_list(bearer_token,account_id):

    url = f"https://us01pbx.zoom.us/api/v2/pbx/account/{account_id}/group"
   
    headers = {
            "Authorization": "{}".format(bearer_token)
        }

    logger.debug("zoom v1 api pbx token {}".format(bearer_token))

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
            
        logger.debug("queue information: {}".format(response.json()))
        return response.json()
     
            
    else:
        logger.debug("Failed to retrieve v1 queue information. Status code: {}".format( response.status_code))
        return None
    
def api_pbx_call_queue_patch(bearer_token,account_id, group_id, json_data):
     
    url = f"https://us01pbx.zoom.us/api/v2/pbx/account/{account_id}/group/{group_id}/exceptionSetting"

    headers = {
            "Authorization": "Bearer {}".format(bearer_token)
        }
    logger.debug("Patching with data: {}".format(json_data))
    response = requests.patch(url, headers=headers, json=json_data)

    if response.status_code == 200:
                
            logger.debug("Patched: {}".format(response.json()))
            return response.json()
     
    else :
            logger.debug("Failed to patch call queue. Status code: {}".format( response.status_code))
            return None
     
     
def api_queue_list(bearer_token):
    url = "https://us01cci.zoom.us/v1/queues/query?size=300"

    headers = {
            "Authorization": "{}".format(bearer_token)
        }

    logger.debug("zoom v1 api token {}".format(bearer_token))

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
            
        logger.debug("queue information: {}".format(response.json()))
        return response
        
            
    else:
        logger.debug("Failed to retrieve v1 queue information. Status code: {}".format( response.status_code))
        return None
     

#return routing-profile id for name
def api_interrupt_menu_update(bearer_token, json_data):
        
        url = "https://us01cci.zoom.us/v1/queues/interruptMenu"
        headers = {
            "Authorization": "{}".format(bearer_token)
        }

        logger.debug("zoom v1 api token {}".format(bearer_token))
        
        logger.debug("json_data: {}".format(json_data))
        body = json_data
        
        req = Request('POST', url, headers=headers, json=body)
        prepared = req.prepare()

        print('URL:', prepared.url)
        print('Headers:', prepared.headers)
        print('Body:', prepared.body)

        s = requests.Session()
        response = s.send(prepared)

        if response.status_code == 200:
            
            logger.debug("interrupt information: {}".format(response.json()))
            if not response.json()['status']:
                return None
            return response
        
            
        else:
            logger.debug("Failed to retrieve agent information. Status code:", response.status_code)
            return None

def api_remote_profile_list(bearer_token):
        
        url = "https://us01cci.zoom.us/v1/routing-profile/agent/query?name"
        headers = {
            "Authorization": "{}".format(bearer_token)
        }

        logger.debug("zoom v1 api token {}".format(bearer_token))
        

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            
            logger.debug("Agent information: {}".format(response.json()))
            return response
        
            
        else:
            logger.debug("Failed to retrieve agent information. Status code: {}".format( response.status_code))
            return None





def agent_profile_id(agent_name):

    response = api_remote_profile_list(session['zoom_v1_token'])
    if response.status_code == 200:
        agent_info = response.json()
        logger.debug("Agent information: {}".format(agent_info))
        remote_profile = json.loads(response.content)
        for profile in remote_profile['result']['records']:
                logger.debug(profile)
                if profile['name'] == agent_name:
                        logger.debug("Profile ID: {}".format(profile['id']))
                        return profile['id']
        return None
    
    else:
        logger.debug("Error retrieving agent information. Status code:", response.status_code)
        return None
    
def v1_queue_id(queue_name):
    response = api_queue_list(session['zoom_v1_token'])
    if response.status_code == 200:
        queue_info = response.json()
        logger.debug("Queue information: {}".format(queue_info))
        queue_list = json.loads(response.content)
        for queue in queue_list['result']['records']:
                logger.debug(queue)
                if queue['name'] == queue_name:
                        logger.debug("Queue ID: {}".format(queue['id']))
                        return queue['id']
        return None
    
    else:
        logger.debug("Error retrieving queue information. Status code:", response.status_code)
        return None
    
def v1_call_queue_id_from_extension(extension, account_id):
    
    page_number = 1
    page_size = 30
    max_pages = 3
    

    while page_number <= max_pages:
        url = f"https://us01pbx.zoom.us/api/v2/pbx/account/{account_id}/group?page_number={page_number}"
        headers = {
            "Authorization": "Bearer {}".format(session['zoom_pbx_token'])
        }

        response = requests.get(url, headers=headers)

        max_pages = response.json()['pageTotal']

        if response.status_code == 200:
            call_queue_info = response.json()
            #logger.debug("Call Queue information: {}".format(call_queue_info))
            call_queue_list = json.loads(response.content)
            for call_queue in call_queue_list['records']:
                logger.debug("Page {} site Name: {}".format(page_number, call_queue['name']))
                logger.debug("Trying to match {} with {}".format(extension, call_queue['extensionNumber']))
                if str(call_queue['extensionNumber']) == str(extension):
                    logger.debug("Call Queue ID: {}".format(call_queue['extensionId']))
                    return call_queue['extensionId'],call_queue['groupId']
            page_number += 1
            logger.debug("incrementing page number to: {}".format(page_number))

        else:
            logger.debug("Error retrieving queue information. Status code:", response.status_code)
            return None,None

    return None,None

def validate_zoom_v1_token():
      
    if session['zoom_v1_token']:
        if api_remote_profile_list(session['zoom_v1_token']): 
            return True
    else:
         return False

def validate_zoom_pbx_token(request):
    zoom_pbx_token = request.session.get('zoom_pbx_token')
    if zoom_pbx_token:
        if get_pbx_account_id(zoom_pbx_token):
            logger.critical("Valid PBX token")
            return True
    else:
        return False

def get_pbx_account_id(bearer_token):
    url = "https://us01pbx.zoom.us/api/v2/pbx/web/userInfo"

    headers = {
       "Authorization": "Bearer {}".format(bearer_token)
    }

    req = Request('GET', url, headers=headers)
    prepared = req.prepare()
    s = requests.Session()
    response = s.send(prepared)

    if response.status_code == 200:
        response_data = response.json()
        logger.critical("Account ID: %s", response_data['accountId'])
        return response_data['accountId']
    else:
        logger.critical("Error retrieving account ID. Status code: %s", response.status_code)
        #logger.critical("Response: %s", response.json())
        return None

def list_auto_receptionists(org_account_info, api_key):
    url = f"https://us01pbx.zoom.us/api/v2/pbx/account/{org_account_info}/auto-receptionist?page_number=1&page_size=15&isLimitRole=true"
    headers = { "Authorization": "Bearer "+ api_key}  # Make sure to replace api_key with the actual API key
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return response.json()


def update_ca_call_handling(bearer_token, json_data, common_area_ext):

    account_id = get_pbx_account_id(bearer_token)
        
    url = f"https://us01pbx.zoom.us/api/v2/pbx/account/{account_id}/extension/{common_area_ext}/call-handling/routing/business_hour_not_answered"
    headers = {
        "Authorization": "Bearer {}".format(bearer_token)
    }
    logger.debug("json_data: {}".format(json_data))
    body = json_data
        
    req = Request('PATCH', url, headers=headers, json=body)

    prepared = req.prepare()

    print('URL:', prepared.url)
    print('Headers:', prepared.headers)
    print('Body:', prepared.body)

    s = requests.Session()
    response = s.send(prepared)

    if response.status_code == 200:
        return response
        
    else:
        logger.debug("Failed to update common area call handling. Status code:{}".format(response.content))
        return None
    
def submit_phone_create_site_to_zoom_api(org_account_info, bearer_token, row):
    url = f"https://us01pbx.zoom.us/api/v2/pbx/account/{org_account_info}phone/site"

    headers = {
        "Authorization": "Bearer " + bearer_token,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=row)
    return response

def submit_phone_create_auto_receptionist_to_zoom_api(org_account_info, token, json_payload):
    url = "https://us01pbx.zoom.us/api/v2/pbx/account/rWTImEw4R72bLLeD6xbznw/auto-receptionist"  # Example URL, adjust to actual endpoint
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json_payload, headers=headers)
    return response

def submit_phone_create_common_area_to_zoom_api(account_id, bearer_token, payload):
    url = f"https://us01pbx.zoom.us/api/v2/pbx/account/{account_id}/commonAreaV2"
      # Example URL, adjust to actual endpoint
    headers = {
        "Authorization": "Bearer " + bearer_token,
        "Content-Type": "application/json"
    }
    response = requests.post(url, payload, headers=headers)
    return response

def get_licenseId(license):
    """Convert plan type name to its numeric code."""

    PLAN_TYPE_MAPPING = {
        "us/ca unlimited": [200],
        "us only": [100],
        "global unlimited": [300]
    }

    if isinstance(license, int):
        # If 'License' is an integer, return it as a list
        return [license]
    else:
        # If 'License' is a string, map it to its numeric code
        return PLAN_TYPE_MAPPING.get(license.strip())


def submit_phone_create_call_queue_to_zoom_api(account_id, bearer_token, payload):
    url = f"https://us01pbx.zoom.us/api/v2/pbx/account/{account_id}/group"
      # Example URL, adjust to actual endpoint
    headers = {
        "Authorization": "Bearer " + bearer_token,
        "Content-Type": "application/json"
    }
    response = requests.post(url, payload, headers=headers)
    return response

def get_user_extensionId(account_id, bearer_token, user_extension_number):
    base_url = f"https://us01pbx.zoom.us/api/v2/pbx/account/{account_id}/extension?page_number=1&page_size=15&withPhoneNumber=true&includeEmergencyAddress=true&module=userZr&operate=Read&isLimitRole=true"
    headers = { "Authorization": "Bearer " + bearer_token }
    
    page_number = 1
    total_pages = None

    (f"Fetching Common Area ID for Display Name '{user_extension}'")  # Debugging line
    while True:
        params = {"page_number": page_number}
        response = requests.get(base_url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"Received non-200 response: {response.status_code}")  # Debugging line
            return None

        data = response.json()
        records = data.get("records", [])
        for record in records:
            if record.get("extensionNumber") == user_extension_number:
                logging.info(f"Extension ID Found: {record.get('extensionId')}")
                return record.get("extensionId")  # Debugging line
            
        if total_pages is None:
            total_pages = data.get("pageTotal", 0)
            logging.info(f"Total pages found: {total_pages}")  # Debugging line

        if page_number >= total_pages:
            logging.info(f"Reached end of pages at page {page_number}")  # Debugging line
            break

        page_number += 1
    logging.info(f"No Extension Id found for Extension Number '{user_extension_number}'")
    return None

def get_common_area_extensionId(org_account_info, bearer_token, common_area_extension_number):
    base_url = f"https://us01pbx.zoom.us/api/v2/pbx/account/{org_account_info}/commonAreaV2?"
    headers = { "Authorization": "Bearer " + bearer_token }
    
    page_number = 1
    total_pages = None

    (f"Fetching Common Area ID for Extension Number '{common_area_extension_number}'")  # Debugging line
    while True:
        params = {"page_number": page_number}
        response = requests.get(base_url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"Received non-200 response: {response.status_code}")  # Debugging line
            return None

        data = response.json()
        records = data.get("records", [])
        for record in records:
            if record.get("extensionNumber") == common_area_extension_number:
                logging.info(f"Extension ID Found: {record.get('extensionId')}")
                return record.get("extensionId")  # Debugging line
            
        if total_pages is None:
            total_pages = data.get("pageTotal", 0)
            logging.info(f"Total pages found: {total_pages}")  # Debugging line

        if page_number >= total_pages:
            logging.info(f"Reached end of pages at page {page_number}")  # Debugging line
            break

        page_number += 1
    logging.info(f"No Extension Id found for CAP Extension '{common_area_extension_number}'")
    return None