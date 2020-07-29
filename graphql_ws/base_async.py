import asyncio
import inspect
from abc import ABC, abstractmethod
from types import CoroutineType, GeneratorType
from typing import Any, Union, List, Dict
from weakref import WeakSet

from graphql.execution.executors.asyncio import AsyncioExecutor
from promise import Promise

from graphql_ws import base

from .constants import GQL_COMPLETE, GQL_CONNECTION_ACK, GQL_CONNECTION_ERROR
from .observable_aiter import setup_observable_extension

setup_observable_extension()
CO_ITERABLE_COROUTINE = inspect.CO_ITERABLE_COROUTINE


# Copied from graphql-core v3.1.0 (graphql/pyutils/is_awaitable.py)
def is_awaitable(value: Any) -> bool:
    """Return true if object can be passed to an ``await`` expression.
    Instead of testing if the object is an instance of abc.Awaitable, it checks
    the existence of an `__await__` attribute. This is much faster.
    """
    return (
        # check for coroutine objects
        isinstance(value, CoroutineType)
        # check for old-style generator based coroutine objects
        or isinstance(value, GeneratorType)
        and bool(value.gi_code.co_flags & CO_ITERABLE_COROUTINE)
        # check for other awaitables (e.g. futures)
        or hasattr(value, "__await__")
    )


async def resolve(
    data: Any, _container: Union[List, Dict] = None, _key: Union[str, int] = None
) -> None:
    """
    Recursively wait on any awaitable children of a data element and resolve any
    Promises.
    """
    if is_awaitable(data):
        data = await data
        if isinstance(data, Promise):
            data = data.value  # type: Any
        if _container is not None:
            _container[_key] = data
    if isinstance(data, dict):
        items = data.items()
    elif isinstance(data, list):
        items = enumerate(data)
    else:
        items = None
    if items is not None:
        children = [resolve(child, _container=data, _key=key) for key, child in items]
        if children:
            await asyncio.wait(children)


class BaseAsyncConnectionContext(base.BaseConnectionContext, ABC):
    def __init__(self, ws, request_context=None):
        super().__init__(ws, request_context=request_context)
        self.pending_tasks = WeakSet()

    @abstractmethod
    async def receive(self):
        raise NotImplementedError("receive method not implemented")

    @abstractmethod
    async def send(self, data):
        ...

    @property
    @abstractmethod
    def closed(self):
        ...

    @abstractmethod
    async def close(self, code):
        ...

    def remember_task(self, task, loop=None):
        self.pending_tasks.add(asyncio.ensure_future(task, loop=loop))
        # Clear completed tasks
        self.pending_tasks -= WeakSet(
            task for task in self.pending_tasks if task.done()
        )


class BaseAsyncSubscriptionServer(base.BaseSubscriptionServer, ABC):
    graphql_executor = AsyncioExecutor

    def __init__(self, schema, keep_alive=True, loop=None):
        self.loop = loop
        super().__init__(schema, keep_alive)

    @abstractmethod
    async def handle(self, ws, request_context=None):
        ...

    def process_message(self, connection_context, parsed_message):
        task = asyncio.ensure_future(
            super().process_message(connection_context, parsed_message)
        )
        connection_context.pending.add(task)
        return task

    async def send_message(self, *args, **kwargs):
        await super().send_message(*args, **kwargs)

    async def on_open(self, connection_context):
        pass

    async def on_connect(self, connection_context, payload):
        pass

    async def on_connection_init(self, connection_context, op_id, payload):
        try:
            await self.on_connect(connection_context, payload)
            await self.send_message(connection_context, op_type=GQL_CONNECTION_ACK)
        except Exception as e:
            await self.send_error(connection_context, op_id, e, GQL_CONNECTION_ERROR)
            await connection_context.close(1011)

    async def on_start(self, connection_context, op_id, params):
        execution_result = self.execute(params)

        if is_awaitable(execution_result):
            execution_result = await execution_result

        if hasattr(execution_result, "__aiter__"):
            iterator = await execution_result.__aiter__()
            connection_context.register_operation(op_id, iterator)
            try:
                async for single_result in iterator:
                    if not connection_context.has_operation(op_id):
                        break
                    await self.send_execution_result(
                        connection_context, op_id, single_result
                    )
            except Exception as e:
                await self.send_error(connection_context, op_id, e)
            connection_context.remove_operation(op_id)
        else:
            try:
                await self.send_execution_result(
                    connection_context, op_id, execution_result
                )
            except Exception as e:
                await self.send_error(connection_context, op_id, e)
        await self.send_message(connection_context, op_id, GQL_COMPLETE)
        await self.on_operation_complete(connection_context, op_id)

    async def on_close(self, connection_context):
        awaitables = tuple(
            self.unsubscribe(connection_context, op_id)
            for op_id in connection_context.operations
        ) + tuple(task.cancel() for task in connection_context.pending_tasks)
        if awaitables:
            try:
                await asyncio.gather(*awaitables, loop=self.loop)
            except asyncio.CancelledError:
                pass

    async def on_stop(self, connection_context, op_id):
        await self.unsubscribe(connection_context, op_id)

    async def on_operation_complete(self, connection_context, op_id):
        pass

    async def send_execution_result(self, connection_context, op_id, execution_result):
        # Resolve any pending promises
        await resolve(execution_result.data)
        await super().send_execution_result(connection_context, op_id, execution_result)
