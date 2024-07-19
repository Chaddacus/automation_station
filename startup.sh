#!/bin/bash

# Determine the project root directory dynamically
PROJECT_ROOT=$(dirname $(dirname $(realpath $0)))

# Export the PYTHONPATH
export PYTHONPATH=$PROJECT_ROOT/automation_station_project

# Start Gunicorn
exec gunicorn --bind=0.0.0.0:8000 --timeout 600 automation_station_project.wsgi:application