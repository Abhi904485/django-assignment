#!/bin/sh

# Run makemigrations
poetry run python manage.py makemigrations

# Run migrate
poetry run python manage.py migrate

# Create superuser automatically if desired (optional)
if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
  poetry run python manage.py createsuperuser --noinput || true
fi

# Start the Django development server
poetry run python manage.py runserver 0.0.0.0:8000
