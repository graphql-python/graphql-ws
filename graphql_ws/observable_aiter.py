
from asyncio import Future, get_event_loop
from rx.internal import extensionmethod
from rx.core import Observable


async def __aiter__(self):
    source = self

    class AIterator:
        def __init__(self):
            self.notifications = []
            self.future = Future()

            self.disposable = source.materialize().subscribe(self.on_next)
            # self.disposed = False

        def __aiter__(self):
            return self

        def dispose(self):
            # self.future.cancel()
            # self.disposed = True
            # self.future.set_exception(StopAsyncIteration)
            self.disposable.dispose()

        def feeder(self):
            if not self.notifications or self.future.done():
                return

            notification = self.notifications.pop(0)
            kind = notification.kind
            if kind == 'N':
                self.future.set_result(notification.value)
            if kind == 'E':
                self.future.set_exception(notification.exception)
            if kind == 'C':
                self.future.set_exception(StopAsyncIteration)

        def on_next(self, notification):
            self.notifications.append(notification)
            self.feeder()

        async def __anext__(self):
            # if self.disposed:
            #     raise StopAsyncIteration
            self.feeder()

            value = await self.future
            self.future = Future()
            return value

    return AIterator()


# def __aiter__(self, sentinel=None):
#     loop = get_event_loop()
#     future = [Future()]
#     notifications = []

#     def feeder():
#         if not len(notifications) or future[0].done():
#             return
#         notification = notifications.pop(0)
#         if notification.kind == "E":
#             future[0].set_exception(notification.exception)
#         elif notification.kind == "C":
#             future[0].set_exception(StopIteration(sentinel))
#         else:
#             future[0].set_result(notification.value)

#     def on_next(value):
#         """Takes on_next values and appends them to the notification queue"""
#         notifications.append(value)
#         loop.call_soon(feeder)

#     self.materialize().subscribe(on_next)

#     @asyncio.coroutine
#     def gen():
#         """Generator producing futures"""
#         loop.call_soon(feeder)
#         future[0] = Future()
#         return future[0]

#     return gen


def setup_observable_extension():
    extensionmethod(Observable)(__aiter__)
