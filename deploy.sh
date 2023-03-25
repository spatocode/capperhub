#!/bin/sh

python manage.py migrate
sudo systemctl restart nginx
sudo service reload nginx
sudo systemctl restart gunicorn