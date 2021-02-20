import os
import shutil

from model import Proxy

SQUID_CONFIG = os.getenv("SQUID_CONFIG")
SQUID_CONFIG_BAK = SQUID_CONFIG + ".souei.bak"
assert SQUID_CONFIG != ""

# PEER_CONF = "cache_peer %s parent %s 0 no-query weighted-round-robin weight=1 connect-fail-limit=2 allow-miss max-conn=5\n"
PEER_CONF = "cache_peer %s parent %s 0 no-query weighted-round-robin weight=1 allow-miss\n"

if not os.path.exists(SQUID_CONFIG_BAK):
    shutil.copyfile(SQUID_CONFIG, SQUID_CONFIG_BAK)


def update_conf(proxies: [Proxy]):
    with open(SQUID_CONFIG_BAK, "r") as F:
        squid_conf = F.readlines()
    squid_conf = list(filter(lambda x: x != "http_access deny all\n", squid_conf))
    squid_conf.append("\n# Cache peer config\n")
    squid_conf.append("http_access allow all\n")
    squid_conf.append("no_cache deny all\n")
    for proxy in proxies:
        ip, port = proxy.ip_port.split(":")
        squid_conf.append(PEER_CONF % (ip, port))
    with open(SQUID_CONFIG, "w") as F:
        F.writelines(squid_conf)

    os.system("squid -k reconfigure")
