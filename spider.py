import asyncio
import base64
import re

import aiohttp
import sqlalchemy
from requests_html import AsyncHTMLSession

from db import sess_maker
from model import Proxy, SCHEME_HTTP, STATUS_NEW
from tool import is_ip_port, proxies, logger


async def run_spider():
    tasks = list()
    for s in [
        ipaddress,
        kuaidaili,
        cool_proxy,
        free_proxy_list,
        http_proxy,
        proxy_list,
        proxy_scraper,
        proxynova,
        pubproxy,
        clarketm_proxy_list,
    ]:
        task = asyncio.ensure_future(s())

        def callback(f):
            sess = sess_maker()
            for p in f.result():
                try:
                    sess.query(Proxy).filter(Proxy.ip_port == p.ip_port).one()
                except sqlalchemy.orm.exc.NoResultFound:
                    if is_ip_port(p.ip_port):
                        sess.add(p)
            sess.commit()

        task.add_done_callback(callback)
        tasks.append(task)
    await asyncio.wait(tasks)


ses = AsyncHTMLSession()


def spider_log(fn):
    async def wrapper(*args, **kw):
        res = await fn(*args, **kw)
        logger.info(f"run spider {fn.__name__} get {len(res)} result")
        return res

    return wrapper


@spider_log
async def ipaddress():
    resp = await ses.get('https://www.ipaddress.com/proxy-list/')
    res = list()
    for ip_row in resp.html.find('.proxylist tbody tr'):
        ip_port = ip_row.find('td:nth-child(1)', first=True).text
        p = Proxy(
            ip_port=ip_port,
            scheme=SCHEME_HTTP,
            status=STATUS_NEW,
        )
        res.append(p)
    return res


@spider_log
async def kuaidaili():
    res = list()
    resp = await ses.get(f'https://www.kuaidaili.com/free/inha/')
    for ip_row in resp.html.find('#list table tr'):
        ip = ip_row.find('td[data-title="IP"]', first=True)
        port = ip_row.find('td[data-title="PORT"]', first=True)
        if ip and port:
            res.append(Proxy(
                ip_port=f"{ip.text}:{port.text}",
                scheme=SCHEME_HTTP,
                status=STATUS_NEW,
            ))
    await asyncio.sleep(5)
    resp = await ses.get(f'https://www.kuaidaili.com/free/intr/')
    for ip_row in resp.html.find('#list table tr'):
        ip = ip_row.find('td[data-title="IP"]', first=True)
        port = ip_row.find('td[data-title="PORT"]', first=True)
        if ip and port:
            res.append(Proxy(
                ip_port=f"{ip.text}:{port.text}",
                scheme=SCHEME_HTTP,
                status=STATUS_NEW,
            ))
    return res


@spider_log
async def cool_proxy():
    async with aiohttp.request(
            "GET",
            'https://cool-proxy.net/proxies.json',
            proxy=proxies
    ) as resp:
        res = await resp.json()
        res = map(lambda x: Proxy(
            ip_port=f"{x['ip']}:{x['port']}",
            scheme=SCHEME_HTTP,
            status=STATUS_NEW,
        ), res)
        return list(res)


@spider_log
async def free_proxy_list():
    resp = await ses.get('https://free-proxy-list.net/')
    res = list()
    for ip_row in resp.html.find('#proxylisttable tbody tr'):
        ip = ip_row.find('td:nth-child(1)', first=True)
        port = ip_row.find('td:nth-child(2)', first=True)
        if ip and port:
            res.append(Proxy(
                ip_port=f"{ip.text}:{port.text}",
                scheme=SCHEME_HTTP,
                status=STATUS_NEW,
            ))
    return res


@spider_log
async def http_proxy():
    res = list()
    for u in [
        'https://proxyhttp.net/free-list/proxy-anonymous-hide-ip-address/',
        'https://proxyhttp.net/',
        'https://proxyhttp.net/free-list/anonymous-server-hide-ip-address/2#proxylist',
    ]:
        resp = await ses.get(u)
        await resp.html.arender(wait=1.5, timeout=10.0)
        for ip_row in resp.html.find('table.proxytbl tr'):
            ip = ip_row.find('td:nth-child(1)', first=True)
            port = ip_row.find('td:nth-child(2)', first=True)
            try:
                if ip and port:
                    port_str = re.search(r'//]]> (\d+)', port.text).group(1)
                    res.append(Proxy(
                        ip_port=f"{ip.text}:{port_str}",
                        scheme=SCHEME_HTTP,
                        status=STATUS_NEW,
                    ))
            except AttributeError:
                pass
    return res


@spider_log
async def proxy_list():
    res = list()
    resp = await ses.get('http://proxy-list.org/english/index.php')

    for ul in resp.html.find('#proxy-table > div.table-wrap ul'):
        js_code = ul.find('li.proxy script', first=True).text
        matched = re.findall(r"Proxy\('(.+)'\)", js_code)
        if matched and len(matched) > 0:
            encoded = matched[0]
            ip_port = base64.b64decode(encoded).decode("utf-8")
            ip = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', ip_port)[0]
            port = re.findall(r':(\d{2,5})', ip_port)[0]
            res.append(Proxy(
                ip_port=f"{ip}:{port}",
                scheme=SCHEME_HTTP,
                status=STATUS_NEW,
            ))

    return res


@spider_log
async def proxy_scraper():
    async with aiohttp.request(
            "GET",
            'https://sunny9577.github.io/proxy-scraper/proxies.json',
            proxy=proxies
    ) as resp:
        res = await resp.json()
        res = map(lambda x: Proxy(
            ip_port=f"{x['ip']}:{x['port']}",
            scheme=SCHEME_HTTP,
            status=STATUS_NEW,
        ), res["proxynova"])
        return list(res)


@spider_log
async def proxynova():
    res = list()
    resp = await ses.get('https://www.proxynova.com/proxy-server-list/')

    for tr in resp.html.find('#tbl_proxy_list > tbody:nth-child(2) > tr'):
        if 'data-proxy-id' not in tr.attrs:
            continue

        script_element = tr.find('td:nth-child(1) > abbr > script', first=True)
        port_element = tr.find('td:nth-child(2)', first=True)
        if not script_element or not port_element:
            continue

        groups = re.findall(
            r"document\.write\('(.*?)'\);",
            script_element.text)
        if not groups or len(groups) != 1:
            continue
        ip = groups[0]
        port = port_element.text
        res.append(Proxy(
            ip_port=f"{ip}:{port}",
            scheme=SCHEME_HTTP,
            status=STATUS_NEW,
        ))

    return res


@spider_log
async def pubproxy():
    async with aiohttp.request(
            "GET",
            'http://pubproxy.com/api/proxy?limit=5&format=json&type=http&level=anonymous&last_check=60',
            proxy=proxies
    ) as resp:
        res = await resp.json()
        res = map(lambda x: Proxy(
            ip_port=f"{x['ipPort']}",
            scheme=SCHEME_HTTP,
            status=STATUS_NEW,
        ), res["data"])
        return list(res)


@spider_log
async def clarketm_proxy_list():
    res = list()
    async with aiohttp.request(
            "GET",
            'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt',
            proxy=proxies
    ) as resp:
        txt = await resp.text()
        ip_port_str_list = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5}', txt)

        for ip_port in ip_port_str_list:

            ip = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', ip_port).group(0)
            port = re.search(r':(\d{2,5})', ip_port).group(1)

            if ip and port:
                res.append(Proxy(
                    ip_port=f"{ip}:{port}",
                    scheme=SCHEME_HTTP,
                    status=STATUS_NEW,
                ))
    return res


@spider_log
async def thespeedx_proxy_list():
    async with aiohttp.request(
            "GET",
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
            proxy=proxies
    ) as resp:
        res = await resp.text()
        res = map(lambda x: Proxy(
            ip_port=f"{x}",
            scheme=SCHEME_HTTP,
            status=STATUS_NEW,
        ), res.split("\n"))
        return list(res)


@spider_log
async def spys_one():
    res = list()
    resp = await ses.get('http://spys.one/en/anonymous-proxy-list')
    await resp.html.arender(wait=1.5, timeout=10.0)
    for ip_row in resp.html.find('table tr[onmouseover]'):
        ip_port_text_elem = ip_row.find('.spy14', first=True)
        if ip_port_text_elem:
            ip_port_text = ip_port_text_elem.text

            ip = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', ip_port_text).group(0)
            port = re.search(r':\n(\d{2,5})', ip_port_text).group(1)

            if ip and port:
                res.append(Proxy(
                    ip_port=f"{ip}:{port}",
                    scheme=SCHEME_HTTP,
                    status=STATUS_NEW,
                ))

    return res
