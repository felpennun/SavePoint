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

# Recommendations are computed by a queue worker (the local stack runs one
# container per algorithm and polls the database every few seconds). Polling
# would keep Neon's serverless compute awake around the clock and burn its free
# hours, so here the API starts a short-lived worker only when a refresh is
# queued (recommendations/ondemand.py): it drains the queue and exits.
export RECOMMENDATION_ONDEMAND_WORKER=1
# Finish whatever an earlier instance left in the queue; the database is awake
# anyway after the migration above, and the process ends when the queue is empty.
python manage.py process_recommendation_jobs --ondemand &

# Warm-up: the first catalogue request after a start computes the filter facets
# (about two seconds) and keeps them in this process's cache for hours. Ask for
# them once the server is listening so the first visitor does not pay for it.
(
  for _ in 1 2 3 4 5 6 7 8 9 10 11 12; do
    sleep 5
    # The Host and X-Forwarded-Proto headers make the request look like one that
    # came through Render's proxy, so host validation and the HTTPS redirect pass.
    python -c "import os,urllib.request; urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:${PORT:-10000}/api/catalogue/games/?facets=lite', headers={'Host': os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost'), 'X-Forwarded-Proto': 'https'}), timeout=60).read()" \
      >/dev/null 2>&1 && break
  done
) &

# Production WSGI server. The Django development server is explicitly
# unsupported for production (no timeouts, no worker recycling, autoreload
# loop) and was flagged in the 2026-09-06 repo review (H-03). gunicorn is a
# pinned, approved dependency (docs/verification/dependency-legitimacy.md).
# One process with four threads leaves room for the on-demand recommendation
# worker in Render Free's 512 MB; the request timeout keeps a stuck request from wedging
# the single instance.
exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-10000}" \
  --workers 1 \
  --threads 4 \
  --timeout 30 \
  --access-logfile - \
  --error-logfile -
