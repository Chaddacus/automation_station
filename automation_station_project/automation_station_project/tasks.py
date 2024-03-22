# tasks.py

from __future__ import absolute_import, unicode_literals
from celery import shared_task
from datetime import datetime
import time
import json


from .helpers import process_csv, init_zoom_client, site_id
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

            #time.sleep(5)
            
        results = {
            "guid": guid,
            "job_result" : job_result,
            "success": success,
            "failed": failed,
            "output": output
        }
            
        async_to_sync(channel_layer.group_send)(
                'job_group',
                {
                    'type': 'job.message',
                    'message': results
                }
            )
        logger.critical("message sent")
        