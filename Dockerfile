FROM python:3.13.1 AS base

WORKDIR /app

ENV PYTHONPATH=/app/src

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY src/ ./src/
COPY scripts/start_server_in_container.sh /app/scripts/start_server_in_container.sh
RUN chmod +x /app/scripts/start_server_in_container.sh

CMD ["bash", "/app/scripts/start_server_in_container.sh"]

