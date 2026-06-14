#!/bin/sh
set -e

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Starting Django dev server on :8000"
exec python manage.py runserver 0.0.0.0:8000
