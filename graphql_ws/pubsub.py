import gevent
import pickle
import redis

from asyncio import Queue
from rx import Observable
from rx.concurrency import GEventScheduler
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
        q = Queue()
        if channel in self.subscriptions:
            self.subscriptions[channel][self.sub_id] = q
        else:
            self.subscriptions[channel] = {self.sub_id: q}
        return self.sub_id, q

    def unsubscribe(self, channel, sub_id):
        if sub_id in self.subscriptions.get(channel, {}):
            del self.subscriptions[channel][sub_id]


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


class GeventRedisPubsub(object):

    def __init__(self, host='localhost', port=6379, *args, **kwargs):
        redis.connection.socket = gevent.socket
        self.redis = redis.StrictRedis(host, port, *args, **kwargs)
        self.subscriptions = {}

    def publish(self, channel, payload):
        self.redis.publish(channel, pickle.dumps(payload))

    def subscribe_to_channel(self, channel):
        if channel in self.subscriptions:
            return self.subscriptions[channel]
        else:
            pubsub = self.redis.pubsub()
            pubsub.subscribe(channel)

            def wait_and_get_messages(observer):
                while True:
                    message = pubsub.get_message(
                        ignore_subscribe_messages=True)
                    if message:
                        observer.on_next(pickle.loads(message['data']))
                    gevent.sleep(.001)

            observable = Observable.create(wait_and_get_messages)\
                .subscribe_on(GEventScheduler())\
                .publish()\
                .auto_connect()

            self.subscriptions[channel] = observable

            return observable
