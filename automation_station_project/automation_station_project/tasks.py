# tasks.py

from __future__ import absolute_import, unicode_literals
from celery import shared_task
from datetime import datetime
import time
import json


from .helpers import process_csv, init_zoom_client, site_id, call_queue_id, common_area_extension_id, site_json, auto_receptionist_id, cc_queue_id, get_role_id
from .v1api import api_pbx_account_info, add_alert_rule, get_site_id, submit_phone_create_site_to_zoom_api, submit_phone_create_auto_receptionist_to_zoom_api, submit_phone_create_common_area_to_zoom_api, get_licenseId
from .v1api import submit_phone_create_call_queue_to_zoom_api
from automation_station.models import Job, JobExecutionLogs
from automation_station.models import ZPCreateSiteV1, CustomUser, ZPCreateAutoReceptionistV1

import logging

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.cache import cache


logger = logging.getLogger(__name__)



@shared_task
def zoom_emergency_alert_notification_v1(guid, data, token):
    output = []
    results = {}
    success = 0
    failed = 0
    job_result = {}

    
    bearer_token = token

        
    account_json = api_pbx_account_info(bearer_token)

    
        
    

    for row in data:

        if account_json:
            account_id = account_json['accountId']
            
        else:
            
            output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            output.append("Error retrieving account id, invalid token, or no account found.")
            output.append("Call Queue Not Created ")
            action_success = False
            failed +=1
            job_result[str(row['id'])] = action_success
            break

        if cache.get(f'stop_task_{guid}'):
            output.append("Task Stopped")
            break

        siteid = get_site_id(bearer_token, account_id, row['target_name'])

        if siteid is None:
            output.append(f"Site {row['target_name']} not found")
            continue

        emails = row['emails'].replace(';', ',').split(',')
        payload = {
            "name": "test3",
            "siteId": siteid,
            "target": siteid,
            "module": 4,
            "type": 19,
            "status": 1,
            "mode": 1,
            "from": "00:00:00",
            "to": "00:00:00",
            "frequency": 0,
            "timezone": "UTC",
            "daysOfWeek": [1, 2, 3, 4, 5, 6, 7],
            "emails": emails,
            "trigger_condition": {
                "event": "emergency call alert",
                "severity": 1
            },
            "targetName": row['target_name']
        }

        response = add_alert_rule(bearer_token, account_id, payload)

        if response.status_code == 200:
            output.append(f"Emergency alert notification for {row['target_name']} created successfully")
            action_success = True
            success += 1
        else:
            output.append(f"Emergency alert notification for {row['target_name']} failed")
            output.append(response.json())
            action_success = False
            failed += 1

        job_result[str(row['id'])] = action_success

    
            
    
    

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
            'job_group',
            {
                'type': 'job.message',
                'message': {
                    'guid': guid,
                    'output': output,
                    'success': success,
                    'failed': failed,
                    'job_result': job_result,
                }
            }
        )

    results = {
        "guid": guid,
        "job_result": job_result,
        "success": success,
        "failed": failed,
        "output": output,
    }

    async_to_sync(channel_layer.group_send)(
        'job_group',
        {
            'type': 'job.message',
            'message': results
        }
    )
    logger.critical("message sent")

@shared_task
def zp_create_site_v1(guid, data, token):
    output = []
    results = {}
    success = 0
    failed = 0
    job_result = {}

    bearer_token = token
    logger.info(f"Bearer token: {bearer_token}")
    account_json = api_pbx_account_info(bearer_token)
    
    for row in data:

        if account_json:
                account_id = account_json['accountId']
                
        else:
                
            output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            output.append("Error retrieving account id, invalid token, or no account found.")
            output.append("Call Queue Not Created ")
            action_success = False
            failed +=1
            job_result[str(row['id'])] = action_success
            break

        if cache.get(f'stop_task_{guid}'):
            output.append("Task Stopped")
            break

        logger.info(f"Processing row {row.get('id')}")

        # Extract necessary fields from the payload
        auto_receptionist_data = row.get('autoReceptionist', {})
        emergency_address_data = row.get('emergencyAddress', {})
        country_info_data = emergency_address_data.get('countryInfo', {})
        country_detail_data = emergency_address_data.get('countryDetail', {})
        site_user = CustomUser.objects.get(id=1)

        # Create CountryInfo instance
        country_info = CountryInfo.objects.create(
            iso_code=country_info_data.get('isoCode', 'US'),
            name=country_info_data.get('name', 'United States'),
            phone_number_support=int(country_info_data.get('phoneNumberSupport', 1)),
            support_toll_free=bool(country_info_data.get('supportTollFree', True)),
            support_toll=bool(country_info_data.get('supportToll', True)),
            has_area_code=bool(country_info_data.get('hasAreaCode', True)),
            order_pn_has_state=bool(country_info_data.get('orderPnHasState', True)),
            order_pn_has_city=bool(country_info_data.get('orderPnHasCity', True)),
            has_state=bool(country_info_data.get('hasState', True)),
            has_city=bool(country_info_data.get('hasCity', True)),
            has_zip=bool(country_info_data.get('hasZip', True)),
            strict_check_address=bool(country_info_data.get('strictCheckAddress', True))
        )
        logger.info(f"CountryInfo created: {country_info}")

        # Create CountryDetail instance
        country_detail = CountryDetail.objects.create(
            iso_code=country_detail_data.get('isoCode', 'US'),
            name=country_detail_data.get('name', 'United States'),
            phone_number_support=int(country_detail_data.get('phoneNumberSupport', 1)),
            support_toll_free=bool(country_detail_data.get('supportTollFree', True)),
            support_toll=bool(country_detail_data.get('supportToll', True)),
            has_area_code=bool(country_detail_data.get('hasAreaCode', True)),
            order_pn_has_state=bool(country_detail_data.get('orderPnHasState', True)),
            order_pn_has_city=bool(country_detail_data.get('orderPnHasCity', True)),
            has_state=bool(country_detail_data.get('hasState', True)),
            has_city=bool(country_detail_data.get('hasCity', True)),
            has_zip=bool(country_detail_data.get('hasZip', True)),
            strict_check_address=bool(country_detail_data.get('strictCheckAddress', True))
        )
        logger.info(f"CountryDetail created: {country_detail}")

        # Create EmergencyAddress instance
        emergency_address = EmergencyAddress.objects.create(
            country=emergency_address_data.get('country', 'US'),
            address_line1=emergency_address_data.get('addressLine1', ''),
            city=emergency_address_data.get('city', ''),
            state_code=emergency_address_data.get('stateCode', ''),
            house_number=emergency_address_data.get('houseNumber', ''),
            street_name=emergency_address_data.get('streetName', ''),
            street_suffix=emergency_address_data.get('streetSuffix', ''),
            pre_directional=emergency_address_data.get('preDirectional', ''),
            post_directional=emergency_address_data.get('postDirectional', ''),
            plus_four=emergency_address_data.get('plusFour', ''),
            level=int(emergency_address_data.get('level', 0)),
            type=int(emergency_address_data.get('type', 0)),
            zip=emergency_address_data.get('zip', ''),
            state_id=emergency_address_data.get('stateId', ''),
            country_info=country_info,
            country_detail=country_detail
        )
        logger.info(f"EmergencyAddress created: {emergency_address}")

        # Create AutoReceptionist instance
        auto_receptionist = AutoReceptionist.objects.create(
            name=auto_receptionist_data.get('name', ''),
            extension_number=auto_receptionist_data.get('extensionNumber', ''),
            open_hour_action=int(auto_receptionist_data.get('openHourAction', 0)),
            close_hour_action=int(auto_receptionist_data.get('closeHourAction', 0)),
            holiday_hour_action=int(auto_receptionist_data.get('holidayHourAction', 0))
        )
        logger.info(f"AutoReceptionist created: {auto_receptionist}")

        # Create ZPCreateSiteV1 instance
        zoom_site = ZPCreateSiteV1.objects.create(
            user=site_user,
            name=row.get('Site Name', ''),
            auto_receptionist=auto_receptionist,
            emergency_address=emergency_address,
            sip_zone_id=row.get('sipZoneId', ''),
            site_code=row.get('siteCode', ''),
            short_extension_length=int(row.get('shortExtensionLength', 0)),
            state_code=row.get('stateCode', ''),
            city=row.get('city', '')
        )
        logger.info(f"Site created: {zoom_site}")

        # Submit the payload to Zoom API
        response = submit_phone_create_site_to_zoom_api(account_id, token, row)
        if response.status_code == 201:
            output.append(f"Site {zoom_site.name} created successfully and submitted to Zoom API")
            action_success = True
            success += 1
        else:
            output.append(f"Site {zoom_site.name} created, but failed to submit to Zoom API: {response.json()}")
            action_success = False
            failed += 1

    job_result[str(row.get('id'))] = action_success

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'job_group',
        {
            'type': 'job.message',
            'message': {
                'guid': guid,
                'output': output,
                'success': success,
                'failed': failed,
                'job_result': job_result,
            }
        }
    )

    results = {
        "guid": guid,
        "job_result": job_result,
        "success": success,
        "failed": failed,
        "output": output,
    }

    async_to_sync(channel_layer.group_send)(
        'job_group',
        {
            'type': 'job.message',
            'message': results
        }
    )
    logger.critical("message sent")

@shared_task
def zp_create_auto_receptionist_v1(guid, data, token):
    output = []
    results = {}
    success = 0
    failed = 0
    job_result = {}

    
    bearer_token = token

        
    account_json = api_pbx_account_info(bearer_token)

    for row in data:

        if account_json:
            account_id = account_json['accountId']
            
        else:
            
            output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            output.append("Error retrieving account id, invalid token, or no account found.")
            output.append("Call Queue Not Created ")
            action_success = False
            failed +=1
            job_result[str(row['id'])] = action_success
            break

        if cache.get(f'stop_task_{guid}'):
            output.append("Task Stopped")
            break

        siteid = get_site_id(bearer_token, account_id, row['siteName'])

        if siteid is None:
            output.append(f"Site {row['siteName']} not found")
            continue

            
            # Prepare payload for AutoReceptionist
        payload = {
            "name": row.get('arName', ''),
            "closeHourAction": int(row.get('closeHourAction', 0)),
            "openHourAction": int(row.get('openHourAction', 0)),
            "holidayHourAction": int(row.get('holidayHourAction', 0)),
            "templateId": row.get('templateId', ''),
            "siteId": "dAMQoIAYRPuhE1uC-q6K2A"
        }
            
            # Convert payload to JSON
        payload_json = json.dumps(payload)
            
            # Submit payload to Zoom API
        response = submit_phone_create_auto_receptionist_to_zoom_api(payload_json, token, account_id)
        if response.status_code == 201:
            output.append(f"Auto Receptionist {payload.get('name')} created successfully and submitted to Zoom API")
            success += 1
            action_success = True
        else:
            output.append(f"Auto Receptionist {payload.get('name')} created, but failed to submit to Zoom API: {response.json()}")
            failed += 1
            action_success = False

        job_result[str(row['id'])] = action_success

    return {
        'guid': guid,
        'output': output,
        'success': success,
        'failed': failed,
        'job_result': job_result
    }

@shared_task
def zp_create_call_queue_v1(guid, data, token):
    output = []
    results = {}
    success = 0
    failed = 0
    job_result = {}

    bearer_token = token

    account_json = api_pbx_account_info(bearer_token)

    for row in data:
        if account_json:
            account_id = account_json['accountId']
        else:
            output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            output.append("Error retrieving account id, invalid token, or no account found.")
            output.append("Call Queue Not Created ")
            action_success = False
            failed += 1
            job_result[str(row['id'])] = action_success
            break

        if cache.get(f'stop_task_{guid}'):
            output.append("Task Stopped")
            break
        
        extensionIds= get_site_id(bearer_token, account_id, row['user_extension_ids'])
        capExtensionIds = get_site_id(bearer_token, account_id, row['common_area_extension_ids'])
        siteid = get_site_id(bearer_token, account_id, row['site_name'])
        extensionNumber = row['extensionNumber']
        name = row['call_queue_name']
        templateId = row['templateId']


        payload = {
        "extensionIds": extensionIds,
        "capExtensionIds": capExtensionIds,
        "name": name,
        "extensionNumber": extensionNumber,
        "templateId": templateId,
        "siteId": siteid
        }

        json_data=json.dumps(payload)

        logger.info(f"Payload: {payload}")
        print(payload)
        response = submit_phone_create_call_queue_to_zoom_api(account_id, bearer_token, json_data)

        if response.status_code == 200:
            output.append(f"Call Queue {name} created successfully")
            action_success = True
            success += 1
        else:
            output.append(f"Failed to create Call Queue for {name}")
            output.append(response.json())
            action_success = False
            failed += 1

        job_result[str(row['id'])] = action_success

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
            'job_group',
            {
                'type': 'job.message',
                'message': {
                    'guid': guid,
                    'output': output,
                    'success': success,
                    'failed': failed,
                    'job_result': job_result,
                }
            }
        )

    results = {
        "guid": guid,
        "job_result": job_result,
        "success": success,
        "failed": failed,
        "output": output,
    }

    async_to_sync(channel_layer.group_send)(
        'job_group',
        {
            'type': 'job.message',
            'message': results
        }
    )
    logger.critical("message sent")

@shared_task
def zp_create_common_area_v1(guid, data, token):
    output = []
    results = {}
    success = 0
    failed = 0
    job_result = {}

    bearer_token = token

    account_json = api_pbx_account_info(bearer_token)

    for row in data:
        if account_json:
            account_id = account_json['accountId']
        else:
            output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            output.append("Error retrieving account id, invalid token, or no account found.")
            output.append("Call Queue Not Created ")
            action_success = False
            failed += 1
            job_result[str(row['id'])] = action_success
            break

        if cache.get(f'stop_task_{guid}'):
            output.append("Task Stopped")
            break
        
        displayName = row.get('displayName')
        siteid = get_site_id(bearer_token, account_id, row['siteName'])
        extensionNumber = row['extensionNumber']
        phoneCountry = row['phoneCountry']
        timeZone = row['timeZone']
        templateId = row['templateId']
        planTypes = get_licenseId(row.get('License'))


        payload = {
        "displayName": displayName,
        "siteId": siteid,
        "extensionNumber": extensionNumber,
        "phoneCountry": phoneCountry,
        "timeZone": timeZone,
        "templateId": templateId,
        "planTypes": planTypes
        }

        json_data=json.dumps(payload)

        logger.info(f"Payload: {payload}")
        print(payload)
        response = submit_phone_create_common_area_to_zoom_api(account_id, bearer_token, json_data)

        if response.status_code == 200:
            output.append(f"Common area for {displayName} created successfully")
            action_success = True
            success += 1
        else:
            output.append(f"Failed to create Common area for {displayName}")
            output.append(response.json())
            action_success = False
            failed += 1

        job_result[str(row['id'])] = action_success

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
            'job_group',
            {
                'type': 'job.message',
                'message': {
                    'guid': guid,
                    'output': output,
                    'success': success,
                    'failed': failed,
                    'job_result': job_result,
                }
            }
        )

    results = {
        "guid": guid,
        "job_result": job_result,
        "success": success,
        "failed": failed,
        "output": output,
    }

    async_to_sync(channel_layer.group_send)(
        'job_group',
        {
            'type': 'job.message',
            'message': results
        }
    )
    logger.critical("message sent")




@shared_task
def add(x, y):
    try:
        logger.critical("add function called")
        return x + y
    except Exception as e:
        logger.exception("Error in add task")

@shared_task
def create_call_queue(guid, data, zoomclientId, zoomclientSecret, zoomaccountId):

        """
        Create call queues in Zoom Phone using a CSV file
        """
        
        output = []
        results = {}
        success = 0
        failed = 0
        job_result = {}
        
        action_success = False
        #reader = process_csv(request, zoomclientId, zoomclientSecret, zoomaccountId, output, action_success)

        client = init_zoom_client(zoomclientId, zoomclientSecret, zoomaccountId)
        for row in data:

            if cache.get(f'stop_task_{guid}'):
                output.append("Task Stopped")
                break
            # Add logic to if/else where jobcollection status = executed if 201 & failed if stop_task or 400
            # Can't access jobs directly here ... should this get built into a map of IDs to status to pass back with results?

            jobcollection = row.pop(0)
            logger.critical(client)
            sId = site_id(row[2], client)
            client_request = client.phone.call_queues_create(name=row[0],site_id=sId,extension_number=row[3])
            
            logger.critical("Processing Call Queue "+row[0])      

            #output.append(client_request.json())

            logger.critical("status code "+ str(client_request.status_code))
            if client_request.status_code == 201:
                logger.critical("Call Queue Created Successfully")
                output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                output.append("Call Queue Created "+row[0])
                output.append(client_request.json())
                success +=1
                action_success = True
            
            else:

                logger.critical("Call Queue Creation Failed")
                logger.critical(client_request.json())
                output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                output.append("Call Queue Not Created "+row[0])
                output.append(client_request.json())
                failed +=1
                action_success = False
            
            job_result[str(jobcollection)] = action_success
            
            channel_layer = get_channel_layer()
            
            logging.critical(channel_layer)

           # time.sleep(2)
            
        results = {
            "guid": guid,
            "job_result" : job_result,
            "success": success,
            "failed": failed,
            "output": output,
        }
            
        async_to_sync(channel_layer.group_send)(
                'job_group',
                {
                    'type': 'job.message',
                    'message': results
                }
            )
        logger.critical("message sent")


@shared_task
def add_call_queue_members(guid, data, zoomclientId, zoomclientSecret, zoomaccountId):
    """
    Add call queue members to Zoom Phone using a CSV file
    """
    output = []
    results = {}
    success = 0
    failed = 0
    job_result = {}

    action_success = False

    client = init_zoom_client(zoomclientId, zoomclientSecret, zoomaccountId)
    for row in data:

        if cache.get(f'stop_task_{guid}'):
            output.append("Task Stopped")
            break

        jobcollection = row.pop(0)

        id = call_queue_id(row[1], client)

        if row[2] and row[3]: 
            output.append("Please provide either a user or a common area, not both in the same row")
        elif row[3]: 
            ca_id = common_area_extension_id(row[3], client)
            dict = {'common_area_ids': [ca_id]}
        else:
            dict = {'users': [{'email': row[2]}]}

        client_request = client.phone.call_queue_members(id=id, members=dict)

        if client_request.status_code == 201:
            action_success = True
            if row[2]:
                output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                output.append(f"Queue Member Added Successfully: {row[2]}")
            if row[3]:
                output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                output.append(f"Queue Member Added Successfully: {row[3]}")
            success += 1
        else:
            if row[2]:
                output.append(f"Queue Member Not Added {row[2]}")
            if row[3]:
                output.append(f"Queue Member Not Added: {row[3]}")
            output.append(client_request.json())
            failed += 1
            action_success = False

        job_result[str(jobcollection)] = action_success

    results = {
        "guid": guid,
        "job_result": job_result,
        "success": success,
        "failed": failed,
        "output": output,
    }

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'job_group',
        {
            'type': 'job.message',
            'message': results
        }
    )


@shared_task
def add_sites(guid, data, zoomclientId, zoomclientSecret, zoomaccountId):
    """
    Add sites to Zoom Phone using a CSV file
    """
    output = []
    results = {}
    success = 0
    failed = 0
    job_result = {}

    action_success = False

    client = init_zoom_client(zoomclientId, zoomclientSecret, zoomaccountId)

    
    for row in data:

        if cache.get(f'stop_task_{guid}'):
            output.append("Task Stopped")
            break

        jobcollection = row.pop(0)

        # Create the data dictionary

        data_dict = {
            "name": row[0],
            "auto_receptionist_name": row[1],
            "default_emergency_address": {
                "country": row[2],
                "address_line1": row[3],
                "city": row[4],
                "zip": row[5],
                "state_code": row[6],
                "address_line2": row[7],
            }, 
            "short_extension_length": row[8], 
            "site_code": row[9]
        }

        #data_dict = site_json(row)

        # Make the client request
        client_request = client.phone.sites(**data_dict)

        if client_request.status_code == 201:
            action_success = True
            output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            output.append(f"Site Added Successfully: {data_dict['name']}")
            success += 1
        else:
            output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            output.append(f"Site Not Added: {data_dict['name']}")
            output.append(client_request.json())
            failed += 1
            action_success = False

        job_result[str(jobcollection)] = action_success

    results = {
        "guid": guid,
        "job_result": job_result,
        "success": success,
        "failed": failed,
        "output": output,
    }

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'job_group',
        {
            'type': 'job.message',
            'message': results
        }
    )       


@shared_task
def add_auto_receptionist(guid, data, zoomclientId, zoomclientSecret, zoomaccountId):

        """
        Create call queues in Zoom Phone using a CSV file
        """
        
        output = []
        results = {}
        success = 0
        failed = 0
        job_result = {}
        
        action_success = False
        #reader = process_csv(request, zoomclientId, zoomclientSecret, zoomaccountId, output, action_success)

        client = init_zoom_client(zoomclientId, zoomclientSecret, zoomaccountId)
        for row in data:

            if cache.get(f'stop_task_{guid}'):
                output.append("Task Stopped")
                break


            jobcollection = row.pop(0)
            logger.critical(client)

            site_id_value = site_id(row[1], client)
            
            params = {
                "name": row[0],
                "site_id": site_id_value
            }

            client_request = client.phone.post_request("/phone/auto_receptionists", data=params)
            
            logger.critical("Processing Auto Receptionist "+row[0])      

            #output.append(client_request.json())

            logger.critical("status code "+ str(client_request.status_code))
            if client_request.status_code == 201:
                logger.critical("Auto Receptionist Added Successfully")
                output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                output.append("Auto Receptionist Added "+row[0])
                output.append(client_request.json())
                success +=1
                action_success = True
            
            else:

                logger.critical("Auto Receptionist Creation Failed")
                logger.critical(client_request.json())
                output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                output.append("Auto Receptionist Not Created "+row[0])
                output.append(client_request.json())
                failed +=1
                action_success = False
            
            job_result[str(jobcollection)] = action_success
            
            channel_layer = get_channel_layer()
            
            logging.critical(channel_layer)

           # time.sleep(2)
            
        results = {
            "guid": guid,
            "job_result" : job_result,
            "success": success,
            "failed": failed,
            "output": output,
        }
            
        async_to_sync(channel_layer.group_send)(
                'job_group',
                {
                    'type': 'job.message',
                    'message': results
                }
            )
        logger.critical("message sent")


@shared_task
def update_auto_receptionist(guid, data, zoomclientId, zoomclientSecret, zoomaccountId):

        """
        Create call queues in Zoom Phone using a CSV file
        """
        
        output = []
        results = {}
        success = 0
        failed = 0
        job_result = {}
        
        action_success = False
        #reader = process_csv(request, zoomclientId, zoomclientSecret, zoomaccountId, output, action_success)

        client = init_zoom_client(zoomclientId, zoomclientSecret, zoomaccountId)
        for row in data:

            if cache.get(f'stop_task_{guid}'):
                output.append("Task Stopped")
                break

            jobcollection = row.pop(0)
            logger.critical(client)

            arId = auto_receptionist_id(row[0], client)
            
            params = {
                'cost_center': row[1],
                'department': row[2],
                'extension_number': row[3],
                'name': row[4],
                'audio_prompt_language': row[5],
                'timezone': row[6]
            }

            client_request = client.phone.patch_request(f"/phone/auto_receptionists/{arId}", data=params)
            
            logger.critical("Processing Auto Receptionist Update "+row[0])      

            #output.append(client_request.json())

            logger.critical("status code "+ str(client_request.status_code))
            if client_request.status_code == 201:
                logger.critical("Auto Receptionist Updated Successfully")
                output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                output.append("Auto Receptionist Updated "+row[0])
                output.append(client_request.json())
                success +=1
                action_success = True
            
            else:

                logger.critical("Auto Receptionist Update Failed")
                logger.critical(client_request.json())
                output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                output.append("Auto Receptionist Not Updated "+row[0])
                output.append(client_request.json())
                failed +=1
                action_success = False
            
            job_result[str(jobcollection)] = action_success
            
            channel_layer = get_channel_layer()
            
            logging.critical(channel_layer)

           # time.sleep(2)
            
        results = {
            "guid": guid,
            "job_result" : job_result,
            "success": success,
            "failed": failed,
            "output": output,
        }
            
        async_to_sync(channel_layer.group_send)(
                'job_group',
                {
                    'type': 'job.message',
                    'message': results
                }
            )
        logger.critical("message sent")

@shared_task
def add_common_areas(guid, data, zoomclientId, zoomclientSecret, zoomaccountId):

        """
        Create call queues in Zoom Phone using a CSV file
        """
        
        output = []
        results = {}
        success = 0
        failed = 0
        job_result = {}
        
        action_success = False
        #reader = process_csv(request, zoomclientId, zoomclientSecret, zoomaccountId, output, action_success)

        client = init_zoom_client(zoomclientId, zoomclientSecret, zoomaccountId)
        for row in data:

            if cache.get(f'stop_task_{guid}'):
                output.append("Task Stopped")
                break


            jobcollection = row.pop(0)
            logger.critical(client)

            site_id_value = site_id(row[4], client)
            
            params = {
                'calling_plans': [
                    {
                        'type': row[0]
                    }
                ],
                'country_iso_code': row[1],
                'display_name': row[2],
                'extension_number': row[3],
                'site_id': site_id_value,
                'timezone': row[5]
            }
            client_request = client.phone.post_request("/phone/common_areas", data=params)
            
            logger.critical("Processing Common Area "+row[2])      

            #output.append(client_request.json())

            logger.critical("status code "+ str(client_request.status_code))
            if client_request.status_code == 201:
                logger.critical("Common Area Added Successfully")
                output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                output.append("Common Area Added "+row[2])
                output.append(client_request.json())
                success +=1
                action_success = True
            
            else:

                logger.critical("Common Area Creation Failed")
                logger.critical(client_request.json())
                output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                output.append("Common Area Not Created "+row[2])
                output.append(client_request.json())
                failed +=1
                action_success = False
            
            job_result[str(jobcollection)] = action_success
            
            channel_layer = get_channel_layer()
            
            logging.critical(channel_layer)

           # time.sleep(2)
            
        results = {
            "guid": guid,
            "job_result" : job_result,
            "success": success,
            "failed": failed,
            "output": output,
        }
            
        async_to_sync(channel_layer.group_send)(
                'job_group',
                {
                    'type': 'job.message',
                    'message': results
                }
            )
        logger.critical("message sent")

@shared_task
def cc_create_call_queue(guid, data, zoomclientId, zoomclientSecret, zoomaccountId):

        """
        Create call queues in Zoom CC using a CSV file
        """
        
        output = []
        results = {}
        success = 0
        failed = 0
        job_result = {}
        
        action_success = False
        #reader = process_csv(request, zoomclientId, zoomclientSecret, zoomaccountId, output, action_success)

        client = init_zoom_client(zoomclientId, zoomclientSecret, zoomaccountId)
        for row in data:

            if cache.get(f'stop_task_{guid}'):
                output.append("Task Stopped")
                break
           
            jobcollection = row.pop(0)
            logger.critical(client)
          

            client_request = client.contact_center.queues_add(queue_name=row[0],queue_description=row[1], queue_type=row[2])
            
            logger.critical("Creating CC Call Queue "+row[0])      

            #output.append(client_request.json())

            logger.critical("status code "+ str(client_request.status_code))
            if client_request.status_code == 201:
                logger.critical("CC Call Queue Created Successfully")
                output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                output.append("CC Call Queue Created "+row[0])
                output.append(client_request.json())
                success +=1
                action_success = True
            
            else:

                logger.critical("CC Call Queue Creation Failed")
                logger.critical(client_request.json())
                output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                output.append("CC Call Queue Not Created "+row[0])
                output.append(client_request.json())
                failed +=1
                action_success = False
            
            job_result[str(jobcollection)] = action_success
            
            channel_layer = get_channel_layer()
            
            logging.critical(channel_layer)

           # time.sleep(2)
            
        results = {
            "guid": guid,
            "job_result" : job_result,
            "success": success,
            "failed": failed,
            "output": output,
        }
            
        async_to_sync(channel_layer.group_send)(
                'job_group',
                {
                    'type': 'job.message',
                    'message': results
                }
            )
        logger.critical("message sent")

@shared_task
def cc_update_call_queue(guid, data, zoomclientId, zoomclientSecret, zoomaccountId):

        """
        Update call queues in Zoom CC using a CSV file
        """
        
        output = []
        results = {}
        success = 0
        failed = 0
        job_result = {}
        
        action_success = False
        #reader = process_csv(request, zoomclientId, zoomclientSecret, zoomaccountId, output, action_success)

        client = init_zoom_client(zoomclientId, zoomclientSecret, zoomaccountId)
        for row in data:

            if cache.get(f'stop_task_{guid}'):
                output.append("Task Stopped")
                break
           
            jobcollection = row.pop(0)
            logger.critical(client)
          
            name = row[0]

            id = cc_queue_id(name, client)

            keys = [
                'queue_name', 'queue_description', 'max_wait_time', 'wrap_up_time', 'max_engagement_in_queue',
                'short_abandon_enable', 'short_abandon_threshold', 'channel_types', 'distribution_type',
                'distribution_duration_in_seconds', 'connecting_media_id', 'transferring_media_id',
                'holding_media_id', 'waiting_room_id', 'message_accept', 'wrap_up_expiration',
                'overflow_to_goodbye_message', 'overflow_to_queue_id', 'overflow_to_flow_id',
                'overflow_to_inbox_id', 'auto_close_message', 'auto_close_message_enabled',
                'auto_close_timeout', 'auto_close_alert_message', 'auto_close_alert_message_enabled',
                'auto_close_alert_message_time', 'recording_storage_location',
                'service_level_threshold_in_seconds', 'service_level_exclude_short_abandoned_calls',
                'service_level_exclude_long_abandoned_calls', 'service_level_exclude_abandoned_quit_engagements',
                'service_level_target_in_percentage', 'agent_routing_profile_id'
            ]

            params = {k: v for k, v in zip(keys, row) if v}
            params['queue_id'] = id

            client_request = client.contact_center.queues_update(**params)
            
            logger.critical("Updating CC Call Queue "+row[0])      

            #output.append(client_request.json())

            logger.critical("status code "+ str(client_request.status_code))
            if client_request.status_code in [200,201,204]:
                logger.critical("CC Call Queue Updated Successfully")
                output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                output.append("CC Call Queue Updated "+row[0] + '\n')
                success +=1
                action_success = True
            
            else:
                logger.critical("CC Call Queue Updated Failed")
                logger.critical(client_request.json())
                output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                output.append("CC Call Queue Not Updated "+row[0]  + '\n')
                output.append(client_request.json())
                failed +=1
                action_success = False
            
            job_result[str(jobcollection)] = action_success
            
            channel_layer = get_channel_layer()
            
            logging.critical(channel_layer)

           # time.sleep(2)
            
        results = {
            "guid": guid,
            "job_result" : job_result,
            "success": success,
            "failed": failed,
            "output": output,
        }
            
        async_to_sync(channel_layer.group_send)(
                'job_group',
                {
                    'type': 'job.message',
                    'message': results
                }
            )
        logger.critical("message sent")

@shared_task
def cc_create_disposition(guid, data, zoomclientId, zoomclientSecret, zoomaccountId):

        """
        Create disposition in Zoom CC using a CSV file
        """
        
        output = []
        results = {}
        success = 0
        failed = 0
        job_result = {}
        
        action_success = False
        #reader = process_csv(request, zoomclientId, zoomclientSecret, zoomaccountId, output, action_success)

        client = init_zoom_client(zoomclientId, zoomclientSecret, zoomaccountId)
        for row in data:

            if cache.get(f'stop_task_{guid}'):
                output.append("Task Stopped")
                break
           
            jobcollection = row.pop(0)
            logger.critical(client)

            keys = ['status','disposition_name','disposition_description','disposition_type','sub_disposition_name','current_index','parent_index']

            params = {k: v for k, v in zip(keys, row) if v}
            client_request = client.contact_center.post_request("/contact_center/dispositions/", data=params)
            
            logger.critical("Creating CC Disposition "+row[1])      

            #output.append(client_request.json())

            logger.critical("status code "+ str(client_request.status_code))
            if client_request is not None and client_request.status_code in [200, 201]:
                logger.critical("CC  Disposition Created Successfully")
                output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                output.append("CC  Disposition Created "+row[1])
                output.append(client_request.json())
                success +=1
                action_success = True
            
            else:

                logger.critical("CC Disposition Creation Failed")
                logger.critical(client_request.json())
                output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                output.append("CC Disposition Not Created "+row[1])
                output.append(client_request.json())
                failed +=1
                action_success = False
            
            job_result[str(jobcollection)] = action_success
            
            channel_layer = get_channel_layer()
            
            logging.critical(channel_layer)

           # time.sleep(2)
            
        results = {
            "guid": guid,
            "job_result" : job_result,
            "success": success,
            "failed": failed,
            "output": output,
        }
            
        async_to_sync(channel_layer.group_send)(
                'job_group',
                {
                    'type': 'job.message',
                    'message': results
                }
            )
        logger.critical("message sent")

@shared_task
def cc_add_users(guid, data, zoomclientId, zoomclientSecret, zoomaccountId):

        """
        Add users in Zoom CC using a CSV file
        """
        
        output = []
        results = {}
        success = 0
        failed = 0
        job_result = {}
        
        action_success = False
        #reader = process_csv(request, zoomclientId, zoomclientSecret, zoomaccountId, output, action_success)

        client = init_zoom_client(zoomclientId, zoomclientSecret, zoomaccountId)
        for row in data:

            if cache.get(f'stop_task_{guid}'):
                output.append("Task Stopped")
                break
           
            jobcollection = row.pop(0)
            logger.critical(client)

            id = get_role_id(row[2], client)

            keys = ['user_id','user_email','role_name','country_iso_code','client_integration','user_access','region_id','channel_settings','multi_channel_engagements','enable','max_agent_load','concurrent_message_capacity']

            params = {k: v for k, v in zip(keys, row) if v}
            params['role_id'] = id

            client_request = client.contact_center.post_request("/contact_center/users/", data=params)  
            
            #logger.critical("Adding CC User "+row[1])      

            #output.append(client_request.json())

            logger.critical("status code "+ str(client_request.status_code))
            if client_request is not None and client_request.status_code in [200, 201]:
                logger.critical("CC User Added Successfully")
                output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                output.append("CC User Added "+row[1])
                output.append(client_request.json())
                success +=1
                action_success = True
            
            else:

                logger.critical("CC User Add Failed")
                logger.critical(client_request.json())
                output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                output.append("CC User Add Failed "+row[1])
                output.append(client_request.json())
                failed +=1
                action_success = False
            
            job_result[str(jobcollection)] = action_success
            
            channel_layer = get_channel_layer()
            
            logging.critical(channel_layer)

           # time.sleep(2)
            
        results = {
            "guid": guid,
            "job_result" : job_result,
            "success": success,
            "failed": failed,
            "output": output,
        }
            
        async_to_sync(channel_layer.group_send)(
                'job_group',
                {
                    'type': 'job.message',
                    'message': results
                }
            )
        logger.critical("message sent")


@shared_task
def cc_create_inbox(guid, data, zoomclientId, zoomclientSecret, zoomaccountId):

        """
        Create disposition in Zoom CC using a CSV file
        """
        
        output = []
        results = {}
        success = 0
        failed = 0
        job_result = {}
        
        action_success = False
        #reader = process_csv(request, zoomclientId, zoomclientSecret, zoomaccountId, output, action_success)

        client = init_zoom_client(zoomclientId, zoomclientSecret, zoomaccountId)
        for row in data:

            if cache.get(f'stop_task_{guid}'):
                output.append("Task Stopped")
                break
           
            jobcollection = row.pop(0)
            logger.critical(client)

            keys = ['inbox_name','inbox_description','inbox_type','inbox_content_storage_location_code','voicemail','soft_delete',
            'soft_delete_days_limit','voicemail_time_limit','delete_voicemail_days_limit','voicemail_transcription','voicemail_notification_by_email',
            'enable','include_voicemail_file','include_voicemail_transcription','forward_voicemail_to_emails','emails']

            params = {k: v for k, v in zip(keys, row) if v}
            client_request = client.contact_center.post_request("/contact_center/inboxes/", data=params)
            
            logger.critical("Creating CC Disposition "+row[0])      

            #output.append(client_request.json())

            logger.critical("status code "+ str(client_request.status_code))
            if client_request is not None and client_request.status_code in [200, 201]:
                logger.critical("CC  Inbox Created Successfully")
                output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                output.append("CC Inbox Created "+row[0])
                output.append(client_request.json())
                success +=1
                action_success = True
            
            else:

                logger.critical("CC Inbox Creation Failed")
                logger.critical(client_request.json())
                output.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                output.append("CC Inbox Not Created "+row[0])
                output.append(client_request.json())
                failed +=1
                action_success = False
            
            job_result[str(jobcollection)] = action_success
            
            channel_layer = get_channel_layer()
            
            logging.critical(channel_layer)

           # time.sleep(2)
            
        results = {
            "guid": guid,
            "job_result" : job_result,
            "success": success,
            "failed": failed,
            "output": output,
        }
            
        async_to_sync(channel_layer.group_send)(
                'job_group',
                {
                    'type': 'job.message',
                    'message': results
                }
            )
        logger.critical("message sent")