FROM python:3.8.5-buster

WORKDIR /src
COPY . /src

RUN pip install -U pip && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-dev

EXPOSE 8080

CMD ["/usr/local/bin/python", "pystream-server.py"]
