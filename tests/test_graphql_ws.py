from collections import OrderedDict

try:
    from unittest import mock
except ImportError:
    import mock

import pytest
from graphql.execution.executors.sync import SyncExecutor

from graphql_ws import base, base_sync, constants


@pytest.fixture
def cc():
    cc = base.BaseConnectionContext(ws=None)
    cc.operations = {"yes": "1"}
    return cc


@pytest.fixture
def ss():
    return base_sync.BaseSyncSubscriptionServer(schema=None)


class TestConnectionContextOperation:
    def test_no_operations_initially(self):
        cc = base.BaseConnectionContext(ws=None)
        assert not cc.operations

    def test_has_operation(self, cc):
        assert cc.has_operation("yes")

    def test_has_operation_missing(self, cc):
        assert not cc.has_operation("no")

    def test_register_operation(self, cc):
        cc.register_operation("new", "2")
        assert "new" in cc.operations

    def test_get_operation(self, cc):
        assert cc.get_operation("yes") == "1"

    def test_remove_operation(self, cc):
        cc.remove_operation("yes")
        assert not cc.operations


class TestConnectionContextNotImplentedMethods:
    def test_receive(self):
        with pytest.raises(NotImplementedError):
            base.BaseConnectionContext(ws=None).receive()

    def test_send(self):
        with pytest.raises(NotImplementedError):
            base.BaseConnectionContext(ws=None).send("TEST")

    def test_closed(self):
        with pytest.raises(NotImplementedError):
            base.BaseConnectionContext(ws=None).closed

    def test_close(self):
        with pytest.raises(NotImplementedError):
            base.BaseConnectionContext(ws=None).close(123)


class TestProcessMessage:
    def test_init(self, ss, cc):
        ss.on_connection_init = mock.Mock()
        ss.process_message(
            cc, {"id": "1", "type": constants.GQL_CONNECTION_INIT, "payload": "payload"}
        )
        ss.on_connection_init.assert_called_with(cc, "1", "payload")

    def test_terminate(self, ss, cc):
        ss.on_connection_terminate = mock.Mock()
        ss.process_message(cc, {"id": "1", "type": constants.GQL_CONNECTION_TERMINATE})
        ss.on_connection_terminate.assert_called_with(cc, "1")

    def test_start(self, ss, cc):
        ss.get_graphql_params = mock.Mock()
        ss.get_graphql_params.return_value = {"params": True}
        cc.has_operation = mock.Mock()
        cc.has_operation.return_value = False
        ss.unsubscribe = mock.Mock()
        ss.on_start = mock.Mock()
        ss.process_message(
            cc, {"id": "1", "type": constants.GQL_START, "payload": {"a": "b"}}
        )
        assert not ss.unsubscribe.called
        ss.on_start.assert_called_with(cc, "1", {"params": True})

    def test_start_existing_op(self, ss, cc):
        ss.get_graphql_params = mock.Mock()
        ss.get_graphql_params.return_value = {"params": True}
        cc.has_operation = mock.Mock()
        cc.has_operation.return_value = True
        cc.unsubscribe = mock.Mock()
        ss.execute = mock.Mock()
        ss.send_message = mock.Mock()
        ss.process_message(
            cc, {"id": "1", "type": constants.GQL_START, "payload": {"a": "b"}}
        )
        assert cc.unsubscribe.called

    def test_start_bad_graphql_params(self, ss, cc):
        ss.get_graphql_params = mock.Mock()
        ss.get_graphql_params.return_value = None
        cc.has_operation = mock.Mock()
        cc.has_operation.return_value = False
        ss.send_error = mock.Mock()
        ss.unsubscribe = mock.Mock()
        ss.on_start = mock.Mock()
        ss.process_message(cc, {"id": "1", "type": None, "payload": {"a": "b"}})
        assert ss.send_error.called
        assert ss.send_error.call_args[0][:2] == (cc, "1")
        assert isinstance(ss.send_error.call_args[0][2], Exception)
        assert not ss.on_start.called

    def test_stop(self, ss, cc):
        ss.on_stop = mock.Mock()
        ss.process_message(cc, {"id": "1", "type": constants.GQL_STOP})
        ss.on_stop.assert_called_with(cc, "1")

    def test_invalid(self, ss, cc):
        ss.send_error = mock.Mock()
        ss.process_message(cc, {"id": "1", "type": "unknown"})
        assert ss.send_error.called
        assert ss.send_error.call_args[0][:2] == (cc, "1")
        assert isinstance(ss.send_error.call_args[0][2], Exception)


def test_get_graphql_params(ss, cc):
    payload = {
        "query": "req",
        "variables": "vars",
        "operationName": "query",
        "context": {},
    }
    params = ss.get_graphql_params(cc, payload)
    assert isinstance(params.pop("executor"), SyncExecutor)
    assert params == {
        "request_string": "req",
        "variable_values": "vars",
        "operation_name": "query",
        "context_value": {},
    }


def test_build_message(ss):
    assert ss.build_message("1", "query", "PAYLOAD") == {
        "id": "1",
        "type": "query",
        "payload": "PAYLOAD",
    }


def test_build_message_partial(ss):
    assert ss.build_message(id="1", op_type=None, payload=None) == {"id": "1"}
    assert ss.build_message(id=None, op_type="query", payload=None) == {"type": "query"}
    assert ss.build_message(id=None, op_type=None, payload="PAYLOAD") == {
        "payload": "PAYLOAD"
    }
    with pytest.raises(AssertionError):
        ss.build_message(id=None, op_type=None, payload=None)


def test_send_execution_result(ss):
    ss.execution_result_to_dict = mock.Mock()
    ss.execution_result_to_dict.return_value = {"res": "ult"}
    ss.send_message = mock.Mock()
    ss.send_message.return_value = "returned"
    assert "returned" == ss.send_execution_result(cc, "1", "result")
    ss.send_message.assert_called_with(cc, "1", constants.GQL_DATA, {"res": "ult"})


def test_execution_result_to_dict(ss):
    result = mock.Mock()
    result.data = "DATA"
    result.errors = "ER"
    result_dict = ss.execution_result_to_dict(result)
    assert isinstance(result_dict, OrderedDict)
    assert result_dict == {
        "data": "DATA",
        "errors": [{"message": "E"}, {"message": "R"}],
    }


def test_send_message(ss, cc):
    ss.build_message = mock.Mock()
    ss.build_message.return_value = {"mess": "age"}
    cc.send = mock.Mock()
    cc.send.return_value = "returned"
    assert "returned" == ss.send_message(cc)
    cc.send.assert_called_with({"mess": "age"})


class TestSSNotImplemented:
    def test_handle(self, ss):
        with pytest.raises(NotImplementedError):
            ss.handle(ws=None, request_context=None)
