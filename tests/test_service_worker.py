import subprocess


def test_service_worker_cache_contract():
    subprocess.run(['node', 'tests/service_worker_harness.js'], check=True)
