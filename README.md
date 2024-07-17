# Cloudwarriors Automation Station 

Django based

  

### config
update the .evn


    

### Database
Create a new database in postgres


    


### settings.py
add your ngrok host to ALLOWED_HOSTS = 

LOGGING_LEVEL = 'CRITICAL' #adjust logging level in settings.py for output



### Commands
```python manage.py makemigrations automation_station```

```python manage.py migrate```

```python manage.py runserver```

or

```python manager.py runserver 0.0.0.0```

```python manage.py createsuperuser #create a superuser for the admin page ```


test