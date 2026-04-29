#!/usr/bin/env bash
# exit on error
set -o errexit

echo "--- Starting build process ---"

echo "--- Installing dependencies ---"
pip install --upgrade pip
pip install -r requirements.txt

# Move into the backend directory where manage.py is
cd backend

echo "--- Collecting static files ---"
python manage.py collectstatic --no-input

echo "--- Applying database migrations ---"
python manage.py migrate

echo "--- Build process completed successfully! ---"
