FROM python:3.10-alpine
COPY . /app
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install -r requirements/prod.txt gunicorn
RUN apk add postgresql-dev
RUN chmod +x entrypoint.sh
ENTRYPOINT ["sh", "entrypoint.sh"]