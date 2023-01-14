FROM python:3.7-slim

WORKDIR /app

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip3 install -r /app/requirements.txt --no-cache-dir

COPY . .