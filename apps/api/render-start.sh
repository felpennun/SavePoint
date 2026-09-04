#!/bin/sh
set -eu

# Render Free has no pre-deploy hook. Keep initialization fail-closed and
# offline: the HTTP listener is exec'd only after every idempotent step passes.
python manage.py migrate --noinput
python manage.py import_catalogue
python manage.py bootstrap_demo_account
python manage.py seed_demo

exec python manage.py runserver "0.0.0.0:${PORT:-10000}"
