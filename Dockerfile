FROM python:3.9-alpine

WORKDIR /app
ADD . /app

RUN apk update --no-cache && \
    apk add squid --no-cache && \
    pip install -r requirements.txt

ENV SQUID_CONFIG="/etc/squid/squid.conf"

EXPOSE 8000
EXPOSE 3128

CMD "squid -s && python main.py"