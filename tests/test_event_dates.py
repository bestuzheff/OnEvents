import os
import subprocess

import pytest


@pytest.mark.parametrize('timezone', ['Pacific/Honolulu', 'Pacific/Kiritimati'])
def test_event_dates_in_browser(timezone):
    env = os.environ.copy()
    env['TZ'] = timezone

    subprocess.run(['node', 'tests/event_dates_harness.js'], check=True, env=env)
