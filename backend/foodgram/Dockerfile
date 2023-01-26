FROM python:3.7-slim

WORKDIR /app

RUN apt-get update && apt-get upgrade -y && pip install --upgrade pip
COPY requirements.txt .
RUN pip3 install -r /app/requirements.txt --no-cache-dir

COPY . .

CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000" ]