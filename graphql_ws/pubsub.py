import asyncio
import pickle

import aredis
import gevent
import redis

from rx.subjects import Subject


class AsyncioPubsub(object):

    def __init__(self):
        self.subscriptions = {}
        self.sub_id = 0

    async def publish(self, channel, payload):
        if channel in self.subscriptions:
            for q in self.subscriptions[channel].values():
                await q.put(payload)

    def subscribe_to_channel(self, channel):
        self.sub_id += 1
        q = asyncio.Queue()
        if channel in self.subscriptions:
            self.subscriptions[channel][self.sub_id] = q
        else:
            self.subscriptions[channel] = {self.sub_id: q}
        return self.sub_id, q

    def unsubscribe(self, channel, sub_id):
        if sub_id in self.subscriptions.get(channel, {}):
            del self.subscriptions[channel][sub_id]
            if not self.subscriptions[channel]:
                del self.subscriptions[channel]


class RxPubsub(object):

    def __init__(self):
        self.subscriptions = {}

    def publish(self, channel, payload):
        if channel in self.subscriptions:
            self.subscriptions[channel].on_next(payload)

    def subscribe_to_channel(self, channel):
        if channel in self.subscriptions:
            return self.subscriptions[channel]
        else:
            subject = Subject()
            self.subscriptions[channel] = subject
            return subject

    def unsubscribe(self, channel, disposable):
        pass


class AsyncioRedisPubsub(object):

    def __init__(self, host='localhost', port=6379, *args, **kwargs):
        self.redis = aredis.StrictRedis(host, port, *args, **kwargs)
        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        self.subscriptions = {}
        self.sub_id = 0
        self.future = None

    async def publish(self, channel, payload):
        await self.redis.publish(channel, pickle.dumps(payload))

    async def subscribe_to_channel(self, channel):
        self.sub_id += 1
        q = asyncio.Queue()
        if channel in self.subscriptions:
            self.subscriptions[channel][self.sub_id] = q
        else:
            await self.pubsub.subscribe(channel)
            self.subscriptions[channel] = {self.sub_id: q}
            if not self.future:
                self.future = asyncio.ensure_future(
                    self._wait_and_get_messages())
        return self.sub_id, q

    def unsubscribe(self, channel, sub_id):
        if sub_id in self.subscriptions.get(channel, {}):
            del self.subscriptions[channel][sub_id]
            if not self.subscriptions[channel]:
                self.pubsub.unsubscribe(channel)
                del self.subscriptions[channel]

    async def _wait_and_get_messages(self):
        while True:
            msg = await self.pubsub.get_message()
            if msg:
                channel = msg['channel'].decode()
                if channel in self.subscriptions:
                    for q in self.subscriptions[channel].values():
                        await q.put(pickle.loads(msg['data']))
            await asyncio.sleep(.001)


class GeventRedisPubsub(object):

    def __init__(self, host='localhost', port=6379, *args, **kwargs):
        redis.connection.socket = gevent.socket
        self.redis = redis.StrictRedis(host, port, *args, **kwargs)
        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        self.subscriptions = {}
        self.greenlet = None

    def publish(self, channel, payload):
        self.redis.publish(channel, pickle.dumps(payload))

    def subscribe_to_channel(self, channel):
        if channel in self.subscriptions:
            return self.subscriptions[channel]
        else:
            self.pubsub.subscribe(channel)
            subject = Subject()
            self.subscriptions[channel] = subject
            if not self.greenlet:
                self.greenlet = gevent.spawn(self._wait_and_get_messages)
            return subject

    def unsubscribe(self, channel, disposable):
        pass

    def _wait_and_get_messages(self):
        while True:
            msg = self.pubsub.get_message()
            if msg:
                if isinstance(msg['channel'], bytes):
                    channel = msg['channel'].decode()
                else:
                    channel = msg['channel']
                if channel in self.subscriptions:
                    self.subscriptions[channel].on_next(pickle.loads(
                        msg['data']))
            gevent.sleep(.001)
