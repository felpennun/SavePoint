#!/bin/sh
set -eu

# Render Free has no pre-deploy hook. Keep initialization fail-closed and
# offline: the HTTP listener is exec'd only after every idempotent step passes.
python manage.py migrate --noinput
python manage.py import_catalogue
python manage.py load_localized_summaries

# The simulated demo accounts are optional: the product no longer needs them
# (people register their own accounts), and the seed contract only exists when
# DEMO_ACCOUNTS is set in the service environment. Without it the old script
# aborted here -- after migrate -- so every deploy since 2026-09-06 failed and
# Render kept serving the previous revision. With it set, both steps stay
# fail-closed exactly as before.
if [ -n "${DEMO_ACCOUNTS:-}" ]; then
  python manage.py bootstrap_demo_accounts
  python manage.py seed_demo
else
  echo "DEMO_ACCOUNTS is not set: skipping the demo account bootstrap and seed."
fi

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
