FROM python:3.12-slim

WORKDIR /worker

COPY requirements-worker.txt .
RUN pip install --no-cache-dir -r requirements-worker.txt

COPY app ./app
COPY runner ./runner

ENV PYTHONPATH=/worker

CMD ["celery", "-A", "app.tasks:celery_app", "worker", "--loglevel=info"]
