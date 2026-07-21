import os
import threading
from wsgiref.simple_server import make_server

import redis as redis_sync
from celery.signals import worker_init
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    multiprocess,
)

# Celery's prefork pool runs several child processes -- if each one
# tried to start its own metrics HTTP server, they'd all fight to bind
# the same port. PROMETHEUS_MULTIPROC_DIR (set in the Dockerfile) makes
# Counter/Histogram write to shared files instead of process-local
# memory; the actual HTTP server below is started exactly once, in
# Celery's main supervisor process, and merges those files on each
# scrape. This is prometheus_client's own documented pattern for
# exactly this situation (originally written for gunicorn workers).

METRICS_PORT = 9100
BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")

submissions_total = Counter(
    "judge_submissions_total",
    "Submissions judged, by language and verdict",
    ["language", "verdict"],
)

judge_duration_seconds = Histogram(
    "judge_duration_seconds",
    "Time to judge a submission, by language",
    ["language"],
)

# multiprocess_mode="livesum" -- sum this gauge's current value across
# all live child processes, since submissions run concurrently across
# the whole pool, not just one process.
active_sandboxes = Gauge(
    "judge_active_sandboxes",
    "Sandbox containers currently running",
    multiprocess_mode="livesum",
)


from prometheus_client.core import GaugeMetricFamily


class _QueueLengthCollector:
    """
    Computed fresh on every scrape, not persisted state -- deliberately
    NOT a prometheus_client.Gauge instance. Instantiating a Gauge here
    would (surprisingly) still get swept into multiprocess file storage
    just because PROMETHEUS_MULTIPROC_DIR is set globally, regardless of
    which registry it's attached to -- which is exactly what caused a
    duplicate judge_queue_length series (once from the file-based
    multiprocess collector, once from this function's own local
    registration). This custom-collector pattern is the documented way
    to add a live, on-demand value alongside multiprocess-tracked ones.
    """

    def collect(self):
        family = GaugeMetricFamily("judge_queue_length", "Pending jobs on the judge queue")
        try:
            r = redis_sync.Redis.from_url(BROKER_URL)
            family.add_metric([], r.llen("celery"))
        except Exception:
            family.add_metric([], -1)  # -1 signals "couldn't measure", not "zero"
        yield family


def _metrics_wsgi_app(environ, start_response):
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    registry.register(_QueueLengthCollector())

    data = generate_latest(registry)
    start_response("200 OK", [("Content-Type", CONTENT_TYPE_LATEST)])
    return [data]


def _serve_metrics():
    httpd = make_server("0.0.0.0", METRICS_PORT, _metrics_wsgi_app)
    httpd.serve_forever()


@worker_init.connect
def start_metrics_server(**kwargs):
    # worker_init fires once, in the main process, before any child
    # workers are forked -- exactly one bind of this port, ever.
    thread = threading.Thread(target=_serve_metrics, daemon=True)
    thread.start()
