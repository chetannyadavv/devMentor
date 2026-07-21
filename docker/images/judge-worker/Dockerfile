FROM python:3.12-slim

WORKDIR /worker

COPY requirements-worker.txt .
RUN pip install --no-cache-dir -r requirements-worker.txt

COPY app ./app
COPY runner ./runner

ENV PYTHONPATH=/worker
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc

# Cleared fresh on every container start -- leftover metric files from a
# previous run would otherwise corrupt what the multiprocess collector
# reads. Deliberately NOT reducing --concurrency here to make metrics
# simpler; that would quietly weaken real concurrent-judging capacity.
CMD mkdir -p $PROMETHEUS_MULTIPROC_DIR && rm -rf $PROMETHEUS_MULTIPROC_DIR/* && \
    celery -A app.tasks:celery_app worker --loglevel=info
