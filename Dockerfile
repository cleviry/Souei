FROM python:3.9

WORKDIR /app
ADD . /app

RUN apt update && \
    apt install -y squid  && \
    apt install -y g++ gcc libxslt-dev make libcurl4-openssl-dev build-essential libssl-dev && \
    apt install -y gconf-service libasound2 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 ca-certificates fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils wget curl && \
    squid -z && \
    pip install -U pip && pip install -r requirements.txt && \
    pyppeteer-install

ENV SQUID_CONFIG="/etc/squid/squid.conf"

EXPOSE 8000
EXPOSE 3128

CMD sh -c "squid -s && python main.py"