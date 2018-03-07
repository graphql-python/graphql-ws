import asyncio
import pickle

import aredis


class AsyncioPubsub:

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


class AsyncioRedisPubsub:

    def __init__(self, host='localhost', port=6379, *args, **kwargs):
        self.redis = aredis.StrictRedis(host, port, *args, **kwargs)
        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        self.subscriptions = {}
        self.sub_id = 0
        self.task = None

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
            if not self.task:
                self.task = asyncio.ensure_future(
                    self._wait_and_get_messages())
        return self.sub_id, q

    async def unsubscribe(self, channel, sub_id):
        if sub_id in self.subscriptions.get(channel, {}):
            del self.subscriptions[channel][sub_id]
        if not self.subscriptions[channel]:
            await self.pubsub.unsubscribe(channel)
            del self.subscriptions[channel]
        if not self.subscriptions:
            self.task.cancel()

    async def _wait_and_get_messages(self):
        while True:
            msg = await self.pubsub.get_message()
            if msg:
                channel = msg['channel'].decode()
                if channel in self.subscriptions:
                    for q in self.subscriptions[channel].values():
                        await q.put(pickle.loads(msg['data']))
            await asyncio.sleep(.001)
