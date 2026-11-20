"""Locust benchmark for Cafe Sedap Nikmat.

Exactly TOTAL_REQUESTS GET or POST attempts are issued. The test runner stops
as soon as the final request finishes. Use gevent's Semaphore rather than
threading.Lock because Locust runs users as cooperative greenlets.
"""
import os
import time
from pathlib import Path

import gevent
from gevent.lock import Semaphore
from locust import HttpUser, task, constant, events

SCENARIO = os.getenv("SCENARIO", "read").lower()
TOTAL_REQUESTS = int(
    os.getenv("TOTAL_REQUESTS", "100" if SCENARIO == "read" else "50")
)
PRODUCT_ID = int(os.getenv("PRODUCT_ID", "1"))

_counter_lock = Semaphore()
_issued = 0
_completed = 0
_test_started_at = None


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    global _issued, _completed, _test_started_at
    _issued = 0
    _completed = 0
    _test_started_at = time.perf_counter()


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    if _test_started_at is None:
        return
    elapsed = time.perf_counter() - _test_started_at
    label = os.getenv("RUN_LABEL", f"{SCENARIO}_test")
    Path("results").mkdir(exist_ok=True)
    output = Path("results/benchmark_durations.csv")
    new_file = not output.exists()
    with output.open("a", encoding="utf-8") as file:
        if new_file:
            file.write("label,scenario,total_requests,total_time_seconds\n")
        file.write(f"{label},{SCENARIO},{TOTAL_REQUESTS},{elapsed:.3f}\n")
    print(f"Benchmark {label}: total waktu {elapsed:.3f} detik")


class CafeUser(HttpUser):
    wait_time = constant(0)

    @task
    def run_scenario(self):
        global _issued, _completed

        # Semaphore aman untuk greenlet Locust; threading.Lock dapat memblokir
        # event loop gevent ketika beberapa virtual user berjalan bersamaan.
        with _counter_lock:
            if _issued >= TOTAL_REQUESTS:
                should_send = False
            else:
                _issued += 1
                should_send = True

        if not should_send:
            # Hindari loop kosong yang terus memakai CPU sambil menunggu
            # request terakhir selesai.
            gevent.sleep(0.01)
            return

        try:
            if SCENARIO == "read":
                self.client.get(
                    "/resource?skip=0&limit=10",
                    name="GET /resource",
                )
            elif SCENARIO == "write":
                self.client.post(
                    "/transactions",
                    json={"product_id": PRODUCT_ID, "qty": 1},
                    name="POST /transactions",
                )
            else:
                raise ValueError("SCENARIO harus bernilai 'read' atau 'write'")
        finally:
            with _counter_lock:
                _completed += 1
                finished = _completed >= TOTAL_REQUESTS

            if finished and self.environment.runner:
                self.environment.runner.quit()
