FROM python:3.10-alpine
COPY . /app
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt gunicorn
RUN apk add postgresql-dev

CMD python manage.py createcachetable && \
    python manage.py migrate --noinput && \
    python manage.py collectstatic --noinput && \
    python manage.py create_super_user && \
    python manage.py crontab add && \
    gunicorn --chdir django_project django_project.wsgi:application --bind 0.0.0.0:8000
