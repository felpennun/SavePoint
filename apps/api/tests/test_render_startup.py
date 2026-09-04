from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_render_start_script_is_fail_closed_and_execs_server_last():
    script = (ROOT / "apps" / "api" / "render-start.sh").read_text(encoding="utf-8")
    expected_steps = [
        "set -eu",
        "python manage.py migrate --noinput",
        "python manage.py import_catalogue",
        "python manage.py bootstrap_demo_account",
        "python manage.py seed_demo",
        'exec python manage.py runserver "0.0.0.0:${PORT:-10000}"',
    ]

    positions = [script.index(step) for step in expected_steps]
    assert positions == sorted(positions)
    assert script.count("exec python manage.py runserver") == 1
