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

# Recommendations are computed by a background queue worker (the local stack
# runs one container per algorithm). Render Free has no worker service, so one
# supervised process runs every job type (signals first, then each section) next
# to the web server; it is restarted if it ever exits (for instance when the
# free instance runs short of memory). Set RECOMMENDATION_WORKER=0 to disable it.
if [ "${RECOMMENDATION_WORKER:-1}" = "1" ]; then
  (
    while true; do
      python manage.py process_recommendation_jobs --loop --poll-seconds 3 || true
      sleep 5
    done
  ) &
fi

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
# One process with four threads leaves room for the recommendation worker in
# Render Free's 512 MB; the request timeout keeps a stuck request from wedging
# the single instance.
exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-10000}" \
  --workers 1 \
  --threads 4 \
  --timeout 30 \
  --access-logfile - \
  --error-logfile -
