import asyncio
from abc import ABC, abstractmethod
from inspect import isawaitable
from weakref import WeakSet

from graphql.execution.executors.asyncio import AsyncioExecutor

from graphql_ws import base

from .constants import GQL_COMPLETE, GQL_CONNECTION_ACK, GQL_CONNECTION_ERROR
from .observable_aiter import setup_observable_extension

setup_observable_extension()


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

    def remember_task(self, task):
        self.pending_tasks.add(asyncio.ensure_future(task))
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
        execution_result = self.execute(connection_context.request_context, params)

        if isawaitable(execution_result):
            execution_result = await execution_result

        if hasattr(execution_result, "__aiter__"):
            iterator = await execution_result.__aiter__()
            connection_context.register_operation(op_id, iterator)
            async for single_result in iterator:
                if not connection_context.has_operation(op_id):
                    break
                await self.send_execution_result(
                    connection_context, op_id, single_result
                )
        else:
            await self.send_execution_result(
                connection_context, op_id, execution_result
            )
        await self.send_message(connection_context, op_id, GQL_COMPLETE)
        await self.on_operation_complete(connection_context, op_id)

    async def on_close(self, connection_context):
        awaitables = tuple(
            self.unsubscribe(connection_context, op_id)
            for op_id in connection_context.operations
        ) + tuple(task.cancel() for task in connection_context.pending_tasks)
        if awaitables:
            await asyncio.gather(*awaitables, loop=self.loop)

    async def on_stop(self, connection_context, op_id):
        await self.unsubscribe(connection_context, op_id)

    async def unsubscribe(self, connection_context, op_id):
        await super().unsubscribe(connection_context, op_id)

    async def on_operation_complete(self, connection_context, op_id):
        pass
