# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster
WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

ENV FLASK_ENV=development
ENV PYTHONUNBUFFERED=0

EXPOSE 5000

COPY . .
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "-p", "5000"]
