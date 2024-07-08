FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 0
ENV PYTHONUNBUFFERED 0

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc

COPY ./backend/post_publisher/requirements/requirements.dev.txt .
RUN pip install --no-cache-dir -r requirements.dev.txt

COPY ./backend/post_publisher .

RUN python manage.py collectstatic --noinput

EXPOSE 8000
