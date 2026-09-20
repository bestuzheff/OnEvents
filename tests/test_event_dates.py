import subprocess


def test_event_dates_in_browser():
    subprocess.run(['node', 'tests/event_dates_harness.js'], check=True)
