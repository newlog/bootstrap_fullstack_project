# Structure

```
~/Documents/code/post_publisher > tree .                                                         00:34:30
.
├── backend
├── compose
│   ├── development
│   │   ├── celery
│   │   │   └── Dockerfile
│   │   ├── django
│   │   │   └── Dockerfile
│   │   └── frontend
│   │       └── Dockerfile
│   └── production
│       ├── celery
│       │   └── Dockerfile
│       ├── django
│       │   └── Dockerfile
│       ├── frontend
│       │   └── Dockerfile
│       └── nginx
│           └── nginx.conf
├── docker-compose.dev.yml
├── docker-compose.prod.yml
└── frontend

13 directories, 9 files
```

# docker-compose.dev.yml

```
services:
  django_post_publisher:
    build:
      context: .
      dockerfile: ./compose/development/django/Dockerfile
    container_name: django_post_publisher
    command: >
      sh -c "python manage.py migrate &&
             python manage.py runserver 0.0.0.0:8000"
    volumes:
      - ./backend/post_publisher:/app
      - post_publisher_static_volume:/app/staticfiles
      - post_publisher_media_volume:/app/media
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=post_publisher.settings
      - PYTHONUNBUFFERED=0
      - PYTHONDONTWRITEBYTECODE=0
    depends_on:
      - redis

  celery:
    build:
      context: .
      dockerfile: ./compose/development/celery/Dockerfile
    container_name: celery
    command: celery -A post_publisher worker --loglevel=info
    volumes:
      - ./backend/post_publisher:/app
    depends_on:
      - redis

  redis:
    image: redis:alpine
    container_name: redis
    ports:
      - "6379:6379"

  frontend_post_publisher:
    build:
      context: .
      dockerfile: ./compose/development/frontend/Dockerfile
    container_name: frontend_post_publisher
    command: npm start
    volumes:
      - ./frontend/post_publisher:/app
      - post_publisher_static_volume:/app/staticfiles
      - post_publisher_media_volume:/app/media
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development

volumes:
  post_publisher_static_volume:
  post_publisher_media_volume:
```

# docker-compose.prod.yml

```
services:
  django_post_publisher:
    build:
      context: .
      dockerfile: ./compose/production/django/Dockerfile
    container_name: django_post_publisher
    command: >
      sh -c "python manage.py migrate &&
             gunicorn --bind 0.0.0.0:8000 post_publisher.wsgi:application"
    volumes:
      - post_publisher_static_volume:/app/staticfiles
      - post_publisher_media_volume:/app/media
    expose:
      - 8000
    environment:
      - DJANGO_SETTINGS_MODULE=post_publisher.settings
      - PYTHONUNBUFFERED=1
      - PYTHONDONTWRITEBYTECODE=1
    depends_on:
      - redis

  celery:
    build:
      context: .
      dockerfile: ./compose/production/celery/Dockerfile
    container_name: celery
    command: celery -A post_publisher worker --loglevel=info
    depends_on:
      - redis

  redis:
    image: redis:alpine
    container_name: redis
    expose:
      - 6379

  frontend_post_publisher:
    build:
      context: .
      dockerfile: ./compose/production/frontend/Dockerfile
    container_name: frontend_post_publisher
    command: nginx -g "daemon off;"
    volumes:
      - post_publisher_static_volume:/usr/share/nginx/html/static
      - post_publisher_media_volume:/usr/share/nginx/html/media
    ports:
      - "80:80"
    environment:
      - NODE_ENV=production
    depends_on:
      - django_post_publisher

volumes:
  post_publisher_static_volume:
  post_publisher_media_volume:
```

# Compose Directory (Development)

## Django Dockerfile

```
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

```

## Frontend Dockerfile

```
FROM node:14
WORKDIR /app
COPY ./frontend/post_publisher/package.json ./frontend/post_publisher/package-lock.json ./
RUN npm install
COPY ./frontend/post_publisher .
RUN npm run build
RUN npm install -g serve
EXPOSE 3000
```

## Celery Dockerfile

```
FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc

COPY ./backend/post_publisher/requirements/requirements.dev.txt .
RUN pip install --no-cache-dir -r requirements.dev.txt

COPY ./backend/post_publisher .

```

# Compose Directory (Production)

## Django Dockerfile

```
FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc

COPY ./backend/post_publisher/requirements/requirements.prod.txt .
RUN pip install --no-cache-dir -r requirements.prod.txt

COPY ./backend/post_publisher .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

```

## Celery Dockerfile

```
FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc

COPY ./backend/post_publisher/requirements/requirements.prod.txt .
RUN pip install --no-cache-dir -r requirements.prod.txt

COPY ./backend/post_publisher .

```

## Frontend Dockerfile

```
# Stage 1: Build the React application
FROM node:14 as build

WORKDIR /app

COPY ./frontend/post_publisher/package.json frontend/post_publisher/package-lock.json ./

RUN npm install

COPY ./frontend/post_publisher .

RUN npm run build

# Stage 2: Serve the React application with Nginx
FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html

COPY compose/production/nginx/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

```

## nginx config

```
# frontend/nginx.conf

server {
    listen 80;

    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        try_files $uri /index.html;
    }

    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }

    location /api/ {
        proxy_pass http://django_post_publisher:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /usr/share/nginx/html/static/;
    }

    location /media/ {
        alias /usr/share/nginx/html/media/;
    }
}

```

# Creating the django app

```
pip install django
cd backend
django-admin startproject mysite
cd mysite
python manage.py startapp myapp
```

For better django project setup, use the cookiecutter from two scoops of django.

## Creating requirements.txt

In the mysite directory create a requirements directory with:

```
# requirements.dev.txt
django
redis
celery
djangorestframework
markdown
django-filter
requests
```

and

```
# requirements.prod.txt
django
redis
celery
djangorestframework
markdown
django-filter
requests
gunicorn
```

## Changing URLs

Adding the api prefix for when we use the production docker compose with nginx (and the proxy pass - redirection - of the frontend requests to the API.&#x20;

urls.py

```
urlpatterns = [
    path('api/admin/', admin.site.urls),
]
```

## Setting up static files

In settings.py

```
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

## Create super user

TBD

# Setting up Celery

## Configure Celery in Django

Create a `celery.py` file in your project directory (where `settings.py` is located):

```python
# mysite/celery.py

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

app = Celery('mysite')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

Add the following configuration to `settings.py`:

```python
# mysite/settings.py

CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'

INSTALLED_APPS = [
    ...
    'myapp',
    ...
]
```

### 3. Define Celery Tasks

Create a `tasks.py` file in your app directory (`posts`)

# Creating the react app

- Install node

  [Node.js — Download Node.js®](https://nodejs.org/en/download/package-manager/current "Node.js — Download Node.js®")

```
# installs nvm (Node Version Manager)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# download and install Node.js (you may need to restart the terminal)
nvm install 22

# verifies the right Node.js version is in the environment
node -v # should print `v22.4.0`

# verifies the right NPM version is in the environment
npm -v # should print `10.8.1`
```

- Create react app

```
npx create-react-app my-react-app
```

<br>

