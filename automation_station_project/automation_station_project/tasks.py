# tasks.py

from __future__ import absolute_import, unicode_literals
from celery import shared_task
from datetime import datetime
import time
import json


from .helpers import process_csv, init_zoom_client, site_id, call_queue_id, common_area_extension_id, site_json
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
            # Add logic to if/else where jobcollection status = executed if 201 & failed if stop_task or 400
            # Can't access jobs directly here ... should this get built into a map of IDs to status to pass back with results?

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
