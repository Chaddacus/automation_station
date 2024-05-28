FROM python:3.11

WORKDIR /code
COPY requirements.txt .
RUN apt-get install -y gcc
RUN pip install -r requirements.txt

COPY ./zoomus ./zoomus
WORKDIR /code/zoomus
RUN pip install .
WORKDIR /code







