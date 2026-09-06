#!/bin/sh
set -eu

# Render Free has no pre-deploy hook. Keep initialization fail-closed and
# offline: the HTTP listener is exec'd only after every idempotent step passes.
python manage.py migrate --noinput
python manage.py import_catalogue
python manage.py bootstrap_demo_accounts
python manage.py seed_demo

# Production WSGI server. The Django development server is explicitly
# unsupported for production (no timeouts, no worker recycling, autoreload
# loop) and was flagged in the 2026-09-06 repo review (H-03). gunicorn is a
# pinned, approved dependency (docs/verification/dependency-legitimacy.md).
# Two sync workers fit Render Free's memory; the request timeout keeps a
# stuck worker from wedging the single instance.
exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-10000}" \
  --workers 2 \
  --timeout 30 \
  --access-logfile - \
  --error-logfile -
