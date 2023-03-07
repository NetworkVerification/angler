# syntax=docker/dockerfile:1
FROM python:3.11-slim-bullseye
WORKDIR /app
RUN apt-get update -y && apt-get install -y cmake gcc g++
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
# ENTRYPOINT [ "python3", "angler.py"]
