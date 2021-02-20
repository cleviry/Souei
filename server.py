from aiohttp import web

from db import sess_maker
from model import Proxy, STATUS_ERROR, STATUS_OK, STATUS_NEW, get_one_proxy, get_all_proxy
from tool import logger

routes = web.RouteTableDef()


@routes.get('/')
async def home(request):
    api = {
        "/": "this page",
        "/one": "get one proxy",
        "/all": "list all proxy",
    }
    try:
        sess = sess_maker()
        available_proxy = sess.query(Proxy).filter(Proxy.status == STATUS_OK).count()
        new_proxy = sess.query(Proxy).filter(Proxy.status == STATUS_NEW).count()
        error_proxy = sess.query(Proxy).filter(Proxy.status == STATUS_ERROR).count()
        sess.close()
        return web.json_response({
            "api": api,
            "status": {
                "available_proxy": available_proxy,
                "new_proxy": new_proxy,
                "error_proxy": error_proxy,
            },
        })
    except:
        return web.json_response({
            "api": api,
            "status": "sql error",
        })


@routes.get('/all')
async def all(request):
    res = get_all_proxy()
    return web.json_response({
        "proxies": list(map(lambda x: x.ip_port, res))
    })


@routes.get('/one')
async def one(request):
    res = get_one_proxy()
    return web.json_response({
        "proxy": res.ip_port
    })


api_server = web.Application()
api_server.add_routes(routes)


async def run_api_server():
    logger.info("run api_server")
    runner = web.AppRunner(api_server)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8000)
    await site.start()
