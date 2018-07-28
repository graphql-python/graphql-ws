from inspect import isawaitable
from graphene_django.settings import graphene_settings
from graphql.execution.executors.asyncio import AsyncioExecutor
from rx import Observer
from ..base import BaseConnectionContext, BaseSubscriptionServer
from ..constants import GQL_CONNECTION_ACK, GQL_CONNECTION_ERROR, GQL_COMPLETE
from ..observable_aiter import setup_observable_extension

setup_observable_extension()


class SubscriptionObserver(Observer):
    def __init__(
        self, connection_context, op_id, send_execution_result, send_error, on_close
    ):
        self.connection_context = connection_context
        self.op_id = op_id
        self.send_execution_result = send_execution_result
        self.send_error = send_error
        self.on_close = on_close

    def on_next(self, value):
        self.send_execution_result(self.connection_context, self.op_id, value)

    def on_completed(self):
        self.on_close(self.connection_context)

    def on_error(self, error):
        self.send_error(self.connection_context, self.op_id, error)


class ChannelsConnectionContext(BaseConnectionContext):
    async def send(self, data):
        await self.ws.send_json(data)

    async def close(self, code):
        await self.ws.close(code=code)


class ChannelsSubscriptionServer(BaseSubscriptionServer):
    def get_graphql_params(self, connection_context, payload):
        payload["context"] = connection_context.request_context
        params = super(ChannelsSubscriptionServer, self).get_graphql_params(
            connection_context, payload
        )
        return dict(params, return_promise=True, executor=AsyncioExecutor())

    async def handle(self, ws, request_context=None):
        connection_context = ChannelsConnectionContext(ws, request_context)
        await self.on_open(connection_context)
        return connection_context

    async def send_message(
        self, connection_context, op_id=None, op_type=None, payload=None
    ):
        message = {}
        if op_id is not None:
            message["id"] = op_id
        if op_type is not None:
            message["type"] = op_type
        if payload is not None:
            message["payload"] = payload

        assert message, "You need to send at least one thing"
        return await connection_context.send(message)

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

        if not hasattr(execution_result, "__aiter__"):
            await self.send_execution_result(
                connection_context, op_id, execution_result
            )
        else:
            iterator = await execution_result.__aiter__()
            connection_context.register_operation(op_id, iterator)
            async for single_result in iterator:
                if not connection_context.has_operation(op_id):
                    break
                await self.send_execution_result(
                    connection_context, op_id, single_result
                )
            await self.send_message(connection_context, op_id, GQL_COMPLETE)

    async def on_close(self, connection_context):
        remove_operations = list(connection_context.operations.keys())
        for op_id in remove_operations:
            self.unsubscribe(connection_context, op_id)

    async def on_stop(self, connection_context, op_id):
        self.unsubscribe(connection_context, op_id)


subscription_server = ChannelsSubscriptionServer(schema=graphene_settings.SCHEMA)