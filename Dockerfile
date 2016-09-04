FROM python:3.5

ENV PYTHONUNBUFFERED 1

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install --default-timeout=1000 --no-cache-dir -r requirements.txt

ADD . /usr/src/app
