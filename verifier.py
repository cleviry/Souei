import asyncio
import os

import aiohttp

from db import sess_maker
from model import Proxy, STATUS_NEW, STATUS_OK, update_proxy_status, STATUS_ERROR
from tool import logger

VERIFY_LIMIT = eval(os.getenv("VERIFY_LIMIT", "0.5"))
DOUBLE_VERIFY_ENABLE = eval(os.getenv("DOUBLE_VERIFY_ENABLE", "True"))
DOUBLE_VERIFY_DELAY = int(os.getenv("DOUBLE_VERIFY_DELAY", 5))
PROXY_TIMEOUT = int(os.getenv("PROXY_TIMEOUT", 5))
VERIFY_URLS = [
    "https://www.baidu.com/",
    "https://www.douban.com/",
    "https://www.163.com/",
    "https://www.sina.com.cn/",
    "https://www.qq.com/",
]

IP_CHECKER_API_SSL = 'https://api.ipify.org/?format=json'

__CURRENT_IP__ = None

semaphore = asyncio.Semaphore(1024)


async def get_current_ip():
    global __CURRENT_IP__
    if __CURRENT_IP__:
        return __CURRENT_IP__
    else:
        async with aiohttp.request(
                "GET", IP_CHECKER_API_SSL,
        ) as resp:
            __CURRENT_IP__ = (await resp.json())['ip']
        return __CURRENT_IP__


async def verify_ip(p: Proxy):
    async with semaphore:
        proxy_url = f"{p.scheme}://{p.ip_port}"
        try:
            async with aiohttp.request(
                    "GET", IP_CHECKER_API_SSL,
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=PROXY_TIMEOUT)
            ) as resp:
                res = await resp.json()
                ip = res["ip"]
                print(ip)
                return STATUS_OK if ip != get_current_ip() else STATUS_ERROR
        except Exception:
            return STATUS_ERROR


async def verify_url(p: Proxy, url):
    async with semaphore:
        proxy_url = f"{p.scheme}://{p.ip_port}"
        try:
            async with aiohttp.request(
                    "GET", url,
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=PROXY_TIMEOUT)
            ) as resp:
                if resp.status == 200:
                    return STATUS_OK
                else:
                    return STATUS_ERROR
        except Exception:
            return STATUS_ERROR


async def verify(p: Proxy):
    tasks = list()
    for u in VERIFY_URLS:
        tasks.append(asyncio.ensure_future(verify_url(p, u)))

    result = await asyncio.gather(*tasks)
    passed = len(list(filter(lambda x: x == STATUS_OK, result))) / len(result)
    logger.debug(f"verify proxy {p.ip_port} passed {passed}")
    result = STATUS_OK if passed >= VERIFY_LIMIT else STATUS_ERROR
    return result


async def proxy_verify(p: Proxy):
    # print(await verify_ip(p))
    res = await verify(p)
    if not DOUBLE_VERIFY_ENABLE:
        return res
    if res == STATUS_ERROR:
        return res
    await asyncio.sleep(DOUBLE_VERIFY_DELAY)
    return await verify(p)


async def verify_and_update(p: Proxy):
    result = await proxy_verify(p)
    logger.debug(f"verify proxy {p.ip_port} status {result}")
    update_proxy_status(p, result)


async def verify_new_proxy():
    s = sess_maker()
    proxies = s.query(Proxy).filter(Proxy.status == STATUS_NEW).all()
    s.close()
    tasks = list()
    for p in proxies:
        tasks.append(asyncio.ensure_future(verify_and_update(p)))
    if tasks:
        await asyncio.wait(tasks)


async def verify_ok_proxy():
    s = sess_maker()
    proxies = s.query(Proxy).filter(Proxy.status == STATUS_OK).all()
    s.close()
    tasks = list()
    for p in proxies:
        tasks.append(asyncio.ensure_future(verify_and_update(p)))
    if tasks:
        await asyncio.wait(tasks)


async def verify_error_proxy():
    s = sess_maker()
    proxies = s.query(Proxy).filter(Proxy.status == STATUS_ERROR).all()
    s.close()
    tasks = list()
    for p in proxies:
        tasks.append(asyncio.ensure_future(verify_and_update(p)))
    if tasks:
        await asyncio.wait(tasks)


async def verify_all_proxy():
    s = sess_maker()
    proxies = s.query(Proxy).all()
    s.close()
    tasks = list()
    for p in proxies:
        tasks.append(asyncio.ensure_future(verify_and_update(p)))
    if tasks:
        await asyncio.wait(tasks)
