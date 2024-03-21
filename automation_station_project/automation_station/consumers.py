from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ZoomPhoneQueue, Job, JobCollection
from django.db.models import Count
from django.core import serializers
from django.template.loader import render_to_string
from asgiref.sync import sync_to_async
from automation_station_project.tasks import create_call_queue
from automation_station_project.helpers import init_zoom_client
from django.forms.models import model_to_dict
import json
import logging


logger = logging.getLogger(__name__)

class JobConsumer(AsyncWebsocketConsumer):
    
    

    def format_data(self, data, keys_to_remove):
        formatted_data = []
        for item in data:
            # Remove specified keys
            for key in keys_to_remove:
                item.pop(key, None)
            # Add the remaining values to the formatted data
            formatted_data.append(list(item.values()))
        return formatted_data

    def get_job_collections(self,job):
        collections = job.Collection.all()
        results = []
        for collection in collections:
            collection_dict = model_to_dict(collection)
            function_name = collection.content_type.model
            logger.critical("function name : "+str(collection.content_object))
            related_object = collection.content_object
            related_object_dict = model_to_dict(related_object) if related_object else None
            collection_dict['related_object'] = related_object_dict
            results.append(collection_dict)
        return results, str(collection.content_object)
    
    def extract_related_objects(self,job_collections):
        return [collection['related_object'] for collection in job_collections if collection['related_object'] is not None]
    
    def get_table_data(self):
    # Get the new data for the table
    # This is just a placeholder - replace this with your actual code
        
        jobs = Job.objects.filter(user=self.scope["user"]).exclude(status__in=['executed', 'deleted']).annotate(rows_count=Count('Collection'))
        completed_jobs = Job.objects.filter(user=self.scope["user"],status='executed').annotate(rows_count=Count('Collection'))
        
        #return render(request, 'jobs.html', {'jobs': jobs, 'completed_jobs': completed_jobs} )
        jobs = render_to_string('job-render/jobs-table.html', {'jobs': jobs})
        completed_jobs = render_to_string('job-render/jobs-completed-table.html', {'completed_jobs': completed_jobs})
        return jobs, completed_jobs
    
    
    
    async def connect(self):
        await self.channel_layer.group_add("job_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("job_group", self.channel_name)
        pass

    async def job_message(self, event):
        message = event['message']
        
        logging.critical(f"Received message!!!!!: {message}")
        
    
    
    async def receive(self, text_data):
        
        logger.critical(f"Received message: {text_data}")
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        logger.critical(f"Received command: {message}")
        message_data = json.loads(text_data_json['message'])
        command = message_data['command']
        
        if command == 'run-selected':
            json_jobs_table, json_completed_jobs = await self.run_selected(message_data)
                       
            
            await self.send(text_data=json.dumps({
            'command': 'update-table',
            'jobs': json_jobs_table,
            'completed_jobs': json_completed_jobs
        }))
        
        if command == 'stop-selected':
            json_jobs_table, json_completed_jobs = await self.stop_selected(message_data)
                       
            
            await self.send(text_data=json.dumps({
            'command': 'update-table',
            'jobs': json_jobs_table,
            'completed_jobs': json_completed_jobs
        }))
            
        if command == 'delete-selected':
            json_jobs_table, json_completed_jobs = await self.delete_selected(message_data)
            
            await self.send(text_data=json.dumps({
            'command': 'update-table',
            'jobs': json_jobs_table,
            'completed_jobs': json_completed_jobs
        }))
            
        elif command == 'redraw':
            json_jobs_table, json_completed_jobs = await self.redraw()
            
            await self.send(text_data=json.dumps({
            'command': 'update-table',
            'jobs': json_jobs_table,
            'completed_jobs': json_completed_jobs
        }))
            
        # Add more commands as needed
        
    @sync_to_async
    
    def run_selected(self, data):
        logger.critical(f"Running selected items: {data}")
        guids = data['guids']
        self.user = self.scope["user"]
        
        for guid in guids:
            
            job = Job.objects.get(job_id=guid)
            
            job.status = "progress"
            
            # Add the logic to run the selected items
            logger.critical(f"Saving job progress {job.job_id}")
            
            job.save()
            
            logging.critical(f"Running job {job.job_id}")
            
            logger.critical(self.user.active_auth)
            
            zoom_auth = self.scope['user'].active_auth
            
            logger.critical(zoom_auth)
            
            data,function_name = self.get_job_collections(job)
            
            logger.critical(data)
            
            related_objects = self.extract_related_objects(data)
            
            logger.critical(related_objects)
            
            keys_to_remove = ['user']
            
            formatted_data = self.format_data(related_objects, keys_to_remove)
            
            logger.critical("here "+str(formatted_data))
            
            client = init_zoom_client(zoom_auth.client_id, zoom_auth.client_secret, zoom_auth.account_id)
            
            #create_call_queue.delay(guid, formatted_data, zoom_auth.client_id, zoom_auth.client_secret, zoom_auth.account_id)
            
            
            logger.critical("function name : "+function_name)
            
            globals()[function_name].delay(guid,
                    formatted_data,
                    zoom_auth.client_id,
                    zoom_auth.client_secret,
                    zoom_auth.account_id
                )
            
            job.status = "executed"
            job.save()

            #create_call_queue(data, zoomclientId, zoomclientSecret, zoomaccountId):
            #get the active auth from the active user
            
            
        jobs, completed_jobs = self.get_table_data()
            
        
        return jobs, completed_jobs
    
    
    @sync_to_async
    
    def stop_selected(self, data):
        guids = data['guids']
        
        for guid in guids:
            job = Job.objects.get(job_id=guid)
            job.status = "executed"
            job.save()
        
        # Add the logic to stop the selected items
        jobs, completed_jobs = self.get_table_data()
            
        
        return jobs, completed_jobs
        
        
        
        
        
    @sync_to_async
        
    def delete_selected(self, data):
        guids = data['guids']
        
        for guid in guids:
            job = Job.objects.get(job_id=guid)
            job.status = "deleted"
            job.save()
        
        # Add the logic to delete the selected items
        jobs, completed_jobs = self.get_table_data()
            
        
        return jobs, completed_jobs
    
    @sync_to_async        
    def redraw(self):
        
        jobs, completed_jobs = self.get_table_data()
            
        
        return jobs, completed_jobs