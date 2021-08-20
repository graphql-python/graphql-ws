from unittest import mock

import json
import promise

import pytest

from graphql_ws import base, base_async

pytestmark = pytest.mark.asyncio


class AsyncMock(mock.MagicMock):
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


class TstServer(base_async.BaseAsyncSubscriptionServer):
    def handle(self, *args, **kwargs):
        pass  # pragma: no cover


@pytest.fixture
def server():
    return TstServer(schema=None)


async def test_terminate(server: TstServer):
    context = AsyncMock()
    await server.on_connection_terminate(connection_context=context, op_id=1)
    context.close.assert_called_with(1011)


async def test_send_error(server: TstServer):
    context = AsyncMock()
    context.has_operation = mock.Mock()
    await server.send_error(connection_context=context, op_id=1, error="test error")
    context.send.assert_called_with(
        {"id": 1, "type": "error", "payload": {"message": "test error"}}
    )


async def test_message(server):
    server.process_message = AsyncMock()
    context = AsyncMock()
    msg = {"id": 1, "type": base.GQL_CONNECTION_INIT, "payload": ""}
    await server.on_message(context, msg)
    server.process_message.assert_called_with(context, msg)


async def test_message_str(server):
    server.process_message = AsyncMock()
    context = AsyncMock()
    msg = {"id": 1, "type": base.GQL_CONNECTION_INIT, "payload": ""}
    await server.on_message(context, json.dumps(msg))
    server.process_message.assert_called_with(context, msg)


async def test_message_invalid(server):
    server.send_error = AsyncMock()
    await server.on_message(connection_context=None, message="'not-json")
    assert server.send_error.called


async def test_resolver(server):
    server.send_message = AsyncMock()
    result = mock.Mock()
    result.data = {"test": [1, 2]}
    result.errors = None
    await server.send_execution_result(
        connection_context=None, op_id=1, execution_result=result
    )
    assert server.send_message.called


@pytest.mark.asyncio
async def test_resolver_with_promise(server):
    server.send_message = AsyncMock()
    result = mock.Mock()
    result.data = {"test": [1, promise.Promise(lambda resolve, reject: resolve(2))]}
    result.errors = None
    await server.send_execution_result(
        connection_context=None, op_id=1, execution_result=result
    )
    assert server.send_message.called
    assert result.data == {"test": [1, 2]}


async def test_resolver_with_nested_promise(server):
    server.send_message = AsyncMock()
    result = mock.Mock()
    inner = promise.Promise(lambda resolve, reject: resolve(2))
    outer = promise.Promise(lambda resolve, reject: resolve({"in": inner}))
    result.data = {"test": [1, outer]}
    result.errors = None
    await server.send_execution_result(
        connection_context=None, op_id=1, execution_result=result
    )
    assert server.send_message.called
    assert result.data == {"test": [1, {"in": 2}]}
