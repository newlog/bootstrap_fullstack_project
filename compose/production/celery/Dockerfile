FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc

COPY ./backend/post_publisher/requirements/requirements.prod.txt .
RUN pip install --no-cache-dir -r requirements.prod.txt

COPY ./backend/post_publisher .
