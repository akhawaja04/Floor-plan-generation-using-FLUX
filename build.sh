#!/usr/bin/env bash
# exit on error
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# Run collect static if needed
python manage.py collectstatic --no-input
python manage.py migrate