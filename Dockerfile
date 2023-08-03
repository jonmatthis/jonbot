FROM python:3.11

WORKDIR /app

ADD . /app

RUN pip install .

EXPOSE 1235

CMD ["python", "jonbot/__main__.py"]
