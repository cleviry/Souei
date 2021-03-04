import datetime

from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

from db import engine, sess_maker
from tool import logger

Base = declarative_base()

STATUS_NEW = "new"
STATUS_OK = "ok"
STATUS_ERROR = "error"

SCHEME_HTTP = "http"
SCHEME_HTTPS = "https"


class Proxy(Base):
    __tablename__ = 'proxy'
    ip_port = Column(String(256), nullable=False, primary_key=True)
    scheme = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)


Base.metadata.create_all(engine)


def get_one_proxy():
    s = sess_maker()
    res = s.query(Proxy).filter(Proxy.status == STATUS_OK).order_by(func.random()).limit(1).one()
    s.close()
    return res


def get_all_proxy():
    s = sess_maker()
    res = s.query(Proxy).filter(Proxy.status == STATUS_OK).all()
    s.close()
    return res


def update_proxy_status(p: Proxy, status):
    logger.debug(f"update {p.ip_port} {p.status} to {status}")
    if p.status != status:
        s = sess_maker()
        s.query(Proxy).filter(Proxy.ip_port == p.ip_port).update({'status': status})
        s.commit()
