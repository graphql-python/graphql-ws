try:
    from aiohttp import WSMsgType
    from graphql_ws.aiohttp import AiohttpConnectionContext, AiohttpSubscriptionServer
except ImportError:  # pragma: no cover
    WSMsgType = None

from unittest import mock

import pytest

from graphql_ws.base import ConnectionClosedException

if_aiohttp_installed = pytest.mark.skipif(
    WSMsgType is None, reason="aiohttp is not installed"
)


class AsyncMock(mock.Mock):
    def __call__(self, *args, **kwargs):
        async def coro():
            return super(AsyncMock, self).__call__(*args, **kwargs)

        return coro()


@pytest.fixture()
def mock_ws():
    ws = AsyncMock(spec=["receive", "send_str", "closed", "close"])
    ws.closed = False
    ws.receive.return_value = AsyncMock(spec=["type", "data"])
    return ws


@if_aiohttp_installed
@pytest.mark.asyncio
class TestConnectionContext:
    async def test_receive_good_data(self, mock_ws):
        msg = mock_ws.receive.return_value
        msg.type = WSMsgType.TEXT
        msg.data = "test"
        connection_context = AiohttpConnectionContext(ws=mock_ws)
        assert await connection_context.receive() == "test"

    async def test_receive_error(self, mock_ws):
        msg = mock_ws.receive.return_value
        msg.type = WSMsgType.ERROR
        connection_context = AiohttpConnectionContext(ws=mock_ws)
        with pytest.raises(ConnectionClosedException):
            await connection_context.receive()

    async def test_receive_closing(self, mock_ws):
        mock_ws.receive.return_value.type = WSMsgType.CLOSING
        connection_context = AiohttpConnectionContext(ws=mock_ws)
        with pytest.raises(ConnectionClosedException):
            await connection_context.receive()

    async def test_receive_closed(self, mock_ws):
        mock_ws.receive.return_value.type = WSMsgType.CLOSED
        connection_context = AiohttpConnectionContext(ws=mock_ws)
        with pytest.raises(ConnectionClosedException):
            await connection_context.receive()

    async def test_send(self, mock_ws):
        connection_context = AiohttpConnectionContext(ws=mock_ws)
        await connection_context.send("test")
        mock_ws.send_str.assert_called_with('"test"')

    async def test_send_closed(self, mock_ws):
        mock_ws.closed = True
        connection_context = AiohttpConnectionContext(ws=mock_ws)
        await connection_context.send("test")
        mock_ws.send_str.assert_not_called()

    async def test_close(self, mock_ws):
        connection_context = AiohttpConnectionContext(ws=mock_ws)
        await connection_context.close(123)
        mock_ws.close.assert_called_with(code=123)


@if_aiohttp_installed
def test_subscription_server_smoke():
    AiohttpSubscriptionServer(schema=None)
