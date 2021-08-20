try:
    from unittest import mock
except ImportError:
    import mock

import json

import pytest

from graphql_ws import base
from graphql_ws.base_sync import SubscriptionObserver


def test_not_implemented():
    server = base.BaseSubscriptionServer(schema=None)
    with pytest.raises(NotImplementedError):
        server.on_connection_init(connection_context=None, op_id=1, payload={})
    with pytest.raises(NotImplementedError):
        server.on_open(connection_context=None)


def test_on_stop():
    server = base.BaseSubscriptionServer(schema=None)
    context = mock.Mock()
    server.on_stop(connection_context=context, op_id=1)
    context.unsubscribe.assert_called_with(1)


def test_terminate():
    server = base.BaseSubscriptionServer(schema=None)

    context = mock.Mock()
    server.on_connection_terminate(connection_context=context, op_id=1)
    context.close.assert_called_with(1011)


def test_send_error():
    server = base.BaseSubscriptionServer(schema=None)
    context = mock.Mock()
    server.send_error(connection_context=context, op_id=1, error="test error")
    context.send.assert_called_with(
        {"id": 1, "type": "error", "payload": {"message": "test error"}}
    )


def test_message():
    server = base.BaseSubscriptionServer(schema=None)
    server.process_message = mock.Mock()
    context = mock.Mock()
    msg = {"id": 1, "type": base.GQL_CONNECTION_INIT, "payload": ""}
    server.on_message(context, msg)
    server.process_message.assert_called_with(context, msg)


def test_message_str():
    server = base.BaseSubscriptionServer(schema=None)
    server.process_message = mock.Mock()
    context = mock.Mock()
    msg = {"id": 1, "type": base.GQL_CONNECTION_INIT, "payload": ""}
    server.on_message(context, json.dumps(msg))
    server.process_message.assert_called_with(context, msg)


def test_message_invalid():
    server = base.BaseSubscriptionServer(schema=None)
    server.send_error = mock.Mock()
    server.on_message(connection_context=None, message="'not-json")
    assert server.send_error.called


def test_context_operations():
    ws = mock.Mock()
    context = base.BaseConnectionContext(ws)
    assert not context.has_operation(1)
    context.register_operation(1, None)
    assert context.has_operation(1)
    context.remove_operation(1)
    assert not context.has_operation(1)
    # Removing a non-existant operation fails silently.
    context.remove_operation(999)


def test_observer_data():
    ws = mock.Mock()
    context = base.BaseConnectionContext(ws)
    send_result, send_error, send_message = mock.Mock(), mock.Mock(), mock.Mock()
    observer = SubscriptionObserver(
        connection_context=context,
        op_id=1,
        send_execution_result=send_result,
        send_error=send_error,
        send_message=send_message,
    )
    observer.on_next("data")
    assert send_result.called
    assert not send_error.called


def test_observer_exception():
    ws = mock.Mock()
    context = base.BaseConnectionContext(ws)
    send_result, send_error, send_message = mock.Mock(), mock.Mock(), mock.Mock()
    observer = SubscriptionObserver(
        connection_context=context,
        op_id=1,
        send_execution_result=send_result,
        send_error=send_error,
        send_message=send_message,
    )
    observer.on_next(TypeError("some bad message"))
    assert send_error.called
    assert not send_result.called
