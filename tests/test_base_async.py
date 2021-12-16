from unittest import mock

import json
import promise

import pytest

from graphql_ws import base, base_async

pytestmark = pytest.mark.asyncio


try:
    from unittest.mock import AsyncMock  # Python 3.8+
except ImportError:
    from mock import AsyncMock


class TstServer(base_async.BaseAsyncSubscriptionServer):
    def handle(self, *args, **kwargs):
        pass  # pragma: no cover


@pytest.fixture
def server():
    return TstServer(schema=None)


async def test_terminate(server: TstServer):
    context = AsyncMock(spec=base_async.BaseAsyncConnectionContext)
    await server.on_connection_terminate(connection_context=context, op_id=1)
    context.close.assert_called_with(1011)


async def test_send_error(server: TstServer):
    context = AsyncMock(spec=base_async.BaseAsyncConnectionContext)
    await server.send_error(connection_context=context, op_id=1, error="test error")
    context.send.assert_called_with(
        {"id": 1, "type": "error", "payload": {"message": "test error"}}
    )


async def test_message(server: TstServer):
    server.process_message = AsyncMock()
    context = AsyncMock(spec=base_async.BaseAsyncConnectionContext)
    msg = {"id": 1, "type": base.GQL_CONNECTION_INIT, "payload": ""}
    await server.on_message(context, msg)
    server.process_message.assert_called_with(context, msg)


async def test_message_str(server: TstServer):
    server.process_message = AsyncMock()
    context = AsyncMock(spec=base_async.BaseAsyncConnectionContext)
    msg = {"id": 1, "type": base.GQL_CONNECTION_INIT, "payload": ""}
    await server.on_message(context, json.dumps(msg))
    server.process_message.assert_called_with(context, msg)


async def test_message_invalid(server: TstServer):
    server.send_error = AsyncMock()
    context = AsyncMock(spec=base_async.BaseAsyncConnectionContext)
    await server.on_message(context, message="'not-json")
    assert server.send_error.called


async def test_resolver(server: TstServer):
    server.send_message = AsyncMock()
    context = AsyncMock(spec=base_async.BaseAsyncConnectionContext)
    result = mock.Mock()
    result.data = {"test": [1, 2]}
    result.errors = None
    await server.send_execution_result(
        context, op_id=1, execution_result=result
    )
    assert server.send_message.called


@pytest.mark.asyncio
async def test_resolver_with_promise(server: TstServer):
    server.send_message = AsyncMock()
    context = AsyncMock(spec=base_async.BaseAsyncConnectionContext)
    result = mock.Mock()
    result.data = {"test": [1, promise.Promise(lambda resolve, reject: resolve(2))]}
    result.errors = None
    await server.send_execution_result(
        context, op_id=1, execution_result=result
    )
    assert server.send_message.called
    assert result.data == {"test": [1, 2]}


async def test_resolver_with_nested_promise(server: TstServer):
    server.send_message = AsyncMock()
    context = AsyncMock(spec=base_async.BaseAsyncConnectionContext)
    result = mock.Mock()
    inner = promise.Promise(lambda resolve, reject: resolve(2))
    outer = promise.Promise(lambda resolve, reject: resolve({"in": inner}))
    result.data = {"test": [1, outer]}
    result.errors = None
    await server.send_execution_result(
        context, op_id=1, execution_result=result
    )
    assert server.send_message.called
    assert result.data == {"test": [1, {"in": 2}]}
