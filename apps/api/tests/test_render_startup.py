from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_render_start_script_is_fail_closed_and_execs_server_last():
    script = (ROOT / "apps" / "api" / "render-start.sh").read_text(encoding="utf-8")
    expected_steps = [
        "set -eu",
        "python manage.py migrate --noinput",
        "python manage.py import_catalogue",
        "python manage.py load_localized_summaries",
        "python manage.py bootstrap_demo_accounts",
        "python manage.py seed_demo",
        "exec gunicorn config.wsgi:application",
    ]

    positions = [script.index(step) for step in expected_steps]
    assert positions == sorted(positions)
    # Exactly one long-lived server process, exec'd (PID 1) after init.
    assert script.count("exec gunicorn") == 1
    # The Django dev server must never be the production process (H-03).
    assert "manage.py runserver" not in script
    assert '--bind "0.0.0.0:${PORT:-10000}"' in script
