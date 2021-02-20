import logging
import os
import re

logger = logging.getLogger("Souei")

IP_REX = re.compile(
    r"^((\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.){3}(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])(?::(?:[0-9]|[1-9][0-9]{1,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5]))?$")

proxies = os.getenv("http_proxy")


def is_ip_port(x: str):
    try:
        return bool(IP_REX.match(x.split(":")[0])) and len(x.split(":")) == 2 and 0 <= int(x.split(":")[1]) <= 65535
    except:
        return False


def cron_wait(fn):
    running = False

    async def wrapper(*args, **kw):
        nonlocal running
        if not running:
            running = True
            res = await fn(*args, **kw)
            running = False
            return res

    return wrapper
