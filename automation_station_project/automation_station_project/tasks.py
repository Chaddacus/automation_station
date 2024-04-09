# tasks.py

from __future__ import absolute_import, unicode_literals
from celery import shared_task
from datetime import datetime
import time
import json


from .helpers import process_csv, init_zoom_client, site_id, call_queue_id, common_area_extension_id, site_json, auto_receptionist_id, cc_queue_id, get_role_id
from automation_station.models import Job, JobExecutionLogs
import logging

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.cache import cache


logger = logging.getLogger(__name__)




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