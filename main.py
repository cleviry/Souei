import asyncio
import logging

from async_cron.job import CronJob
from async_cron.schedule import Scheduler

import spider
import squid
import verifier
from db import sess_maker
from model import Proxy, STATUS_OK
from server import run_api_server
from tool import logger, cron_wait
from verifier import verify_error_proxy

logging.basicConfig(
    level=logging.INFO,
    datefmt='%Y/%m/%d %H:%M:%S',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

VERIFY_ERROR_LIMIT = 10


@cron_wait
async def fetch_new_proxy_task():
    logger.info("run fetch_new_proxy_task")
    await spider.run_spider()
    await verifier.verify_new_proxy()


@cron_wait
async def verify_ok_proxy_task():
    logger.info("run verify_ok_proxy_task")
    await verifier.verify_ok_proxy()


@cron_wait
async def verify_error_proxy_task():
    logger.info("run verify_error_proxy_task")
    s = sess_maker()
    c = s.query(Proxy).filter(Proxy.status == STATUS_OK).count()
    s.close()
    if c < VERIFY_ERROR_LIMIT:
        await verify_error_proxy()


@cron_wait
async def update_squid_task():
    logger.info("run update_squid_task")
    s = sess_maker()
    proxies = s.query(Proxy).filter(Proxy.status == STATUS_OK).all()
    s.close()
    squid.update_conf(proxies)


@cron_wait
async def main_task():
    await verify_ok_proxy_task()
    await fetch_new_proxy_task()
    await verify_error_proxy_task()
    await update_squid_task()


if __name__ == '__main__':
    logger.info("start")

    loop = asyncio.get_event_loop()

    msh = Scheduler()
    msh.add_job(CronJob().every(30).minute.go(main_task))
    # msh.add_job(CronJob().every(10).minute.go(fetch_new_proxy_task))
    # msh.add_job(CronJob().every(5).minute.go(verify_ok_proxy_task))
    # msh.add_job(CronJob().every(30).minute.go(verify_error_proxy_task))
    try:
        loop.run_until_complete(asyncio.wait([
            msh.start(),
            run_api_server(),
        ]))
        loop.run_forever()
    except KeyboardInterrupt:
        print('exit')

    # loop.run_until_complete(update_squid_task())

    # res = loop.run_until_complete(spider.http_proxy())
    # print(list(map(lambda x: x.ip_port, res)))

    # loop.run_until_complete(verifier.verify_error_proxy())
    # loop.run_until_complete(verifier.verify_ok_proxy())
    # loop.run_until_complete(spider.run_spider())
    # loop.run_until_complete(verifier.verify_new_proxy())

    # loop.run_until_complete(update_squid_task())
