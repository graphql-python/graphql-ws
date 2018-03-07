import sys

from .gevent_observable import GeventRxPubsub, GeventRxRedisPubsub

if sys.version_info[0] > 2:
    from .asyncio import AsyncioPubsub, AsyncioRedisPubsub
