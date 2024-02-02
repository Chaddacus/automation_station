Cloudwarriors Automation Station 

Django based

Create a new database in postgres

update the .evn_template

add your ngrok host to ALLOWED_HOSTS = , in settings.py

python manage.py makemigrations automation_station

python manage.py migrate

python manage.py runserver

or

python manager.py runserver 0.0.0.0

python manage.py createsuperuser #create a superuser for the admin page


