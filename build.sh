#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
mkdir -p staticfiles
echo "=== Checking static folder ==="
ls -la static/ || echo "static/ NOT FOUND"
ls -la static/css/ || echo "static/css/ NOT FOUND"
python manage.py collectstatic --no-input --verbosity 2
python manage.py migrate
python manage.py createsuperuser --noinput || true