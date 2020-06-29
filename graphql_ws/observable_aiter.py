from asyncio import Future

from rx.core import Observable
from rx.internal import extensionmethod


async def __aiter__(self):
    source = self

    class AIterator:
        def __init__(self):
            self.notifications = []
            self.future = Future()

            self.disposable = source.materialize().subscribe(self.on_next)

        def __aiter__(self):
            return self

        def dispose(self):
            self.disposable.dispose()

        def feeder(self):
            if not self.notifications or self.future.done():
                return

            notification = self.notifications.pop(0)
            kind = notification.kind
            if kind == "N":
                self.future.set_result(notification.value)
            if kind == "E":
                self.future.set_exception(notification.exception)
            if kind == "C":
                self.future.set_exception(StopAsyncIteration)

        def on_next(self, notification):
            self.notifications.append(notification)
            self.feeder()

        async def __anext__(self):
            self.feeder()

            value = await self.future
            self.future = Future()
            return value

    return AIterator()


def setup_observable_extension():
    extensionmethod(Observable)(__aiter__)
