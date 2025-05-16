import ssl

from decouple import config
from redis import ConnectionPool, Redis

REDIS_URL = config("REDIS_URL")
REDIS_CONNECTION_POOL = ConnectionPool.from_url(REDIS_URL, ssl_cert_reqs=ssl.CERT_NONE)
REDIS_CLIENT = Redis(connection_pool=REDIS_CONNECTION_POOL)
