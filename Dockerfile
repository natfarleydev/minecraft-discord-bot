FROM python:3.10

WORKDIR /work

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

RUN python main.py