try:
    from unittest import mock
except ImportError:
    import mock

from graphql_ws.gevent import GeventConnectionContext, GeventSubscriptionServer


class TestConnectionContext:
    def test_receive(self):
        ws = mock.Mock()
        connection_context = GeventConnectionContext(ws=ws)
        connection_context.receive()
        ws.receive.assert_called()

    def test_send(self):
        ws = mock.Mock()
        ws.closed = False
        connection_context = GeventConnectionContext(ws=ws)
        connection_context.send({"text": "test"})
        ws.send.assert_called_with('{"text": "test"}')

    def test_send_closed(self):
        ws = mock.Mock()
        ws.closed = True
        connection_context = GeventConnectionContext(ws=ws)
        connection_context.send("test")
        assert not ws.send.called

    def test_close(self):
        ws = mock.Mock()
        connection_context = GeventConnectionContext(ws=ws)
        connection_context.close(123)
        ws.close.assert_called_with(123)


def test_subscription_server_smoke():
    GeventSubscriptionServer(schema=None)
