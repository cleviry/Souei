FROM python:3.9

WORKDIR /app
ADD . /app

RUN apt update && \
    apt install squid && \
    squid -z && \
    pip install -r requirements.txt && \
    pyppeteer-install

ENV SQUID_CONFIG="/etc/squid/squid.conf"

EXPOSE 8000
EXPOSE 3128

CMD sh -c "squid -s && python main.py"