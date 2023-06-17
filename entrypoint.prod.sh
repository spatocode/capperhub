#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z "$RDS_HOST" "$RDS_PORT"; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

python manage.py migrate

exec "$@"