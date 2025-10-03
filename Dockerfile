FROM python:3.13.1 AS base

WORKDIR /app

ENV PYTHONPATH=/app/src

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY src/ ./src/

CMD ["bash", "-c", "python src/manage.py migrate && python src/manage.py runserver 0.0.0.0:8000"]

