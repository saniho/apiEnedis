"""Tests for myClientEnedis - no HA dependency."""
import datetime
from unittest.mock import MagicMock

import pytest

from custom_components.myEnedis.myClientEnedis import myClientEnedis


@pytest.fixture
def client():
    return myClientEnedis("myToken", "myPDL")


class TestInit:
    def test_default_values(self, client):
        assert client.getVersion() == "0.0.0"
        assert client.getNbCall() == 0
        assert client.getUpdateRealise() is False
        assert client.getServiceEnedis() == "enedisGateway"
        assert client.getStatusLastCall() is None
        assert client.getErrorLastCall() is None
        assert client.getTimeLastCall() is None
        assert client.getLastUpdate() is None

    def test_custom_init(self):
        c = myClientEnedis(
            "t", "p", delay=7200, version="2.0.0", serviceEnedis="custom"
        )
        assert c.getVersion() == "2.0.0"
        assert c.getServiceEnedis() == "custom"

    def test_hc_hp_cost_init(self):
        c = myClientEnedis(
            "t", "p", heuresCreusesCost=0.1, heuresPleinesCost=0.2
        )
        assert c.getHCCost(100) == 10.0
        assert c.getHPCost(100) == 20.0


class TestTypeDetection:
    def test_is_consommation_default(self, client):
        assert client.isConsommation() is True

    def test_is_production_default(self, client):
        assert client.isProduction() is True


class TestGettersSetters:
    def test_set_nb_call(self, client):
        client.setNbCall(42)
        assert client.getNbCall() == 42

    def test_set_update_realise(self, client):
        client.setUpdateRealise(True)
        assert client.getUpdateRealise() is True

    def test_set_path_archive(self, client):
        client.setPathArchive("/tmp/test")
        assert client.getPathArchive() == "/tmp/test"

    def test_data_json_value_roundtrip(self, client):
        client.setDataJsonValue("key1", {"val": 123})
        assert client.getDataJsonValue("key1") == {"val": 123}
        assert "key1" in client.getDataJsonKeys()

    def test_data_json_default(self, client):
        assert client.getDataJsonValue("nonexistent", default=42) == 42

    def test_data_request_json_roundtrip(self, client):
        obj = MagicMock()
        obj.some_attr = "test"
        client.setDataRequestJson("req_key", obj)
        result = client.getDataRequestJson("req_key")
        assert result.some_attr == "test"


class TestErrorTracking:
    def test_update_error_last_call(self, client):
        client.updateErrorLastCall("test_error")
        assert client.getErrorLastCall() == "test_error"

    def test_set_error_last_call(self, client):
        client.setErrorLastCall("direct_error")
        assert client.getErrorLastCall() == "direct_error"

    def test_update_status_last_call(self, client):
        client.updateStatusLastCall(True)
        assert client.getStatusLastCall() is True

    def test_get_card_error_default(self, client):
        assert client.getCardErrorLastCall() == ""

    def test_set_nb_call_tracking(self, client):
        client.setNbCall(5)
        assert client.getNbCall() == 5
        client.setNbCall(10)
        assert client.getNbCall() == 10


class TestLastMethodCall:
    def test_default_last_method_call(self, client):
        assert client.lastMethodCall is None

    def test_set_last_method_call(self, client):
        client.lastMethodCall = "updateYesterday"
        assert client.lastMethodCall == "updateYesterday"

    def test_last_method_call_error_default(self, client):
        assert client.lastMethodCallError is None

    def test_set_last_method_call_error(self, client):
        client.lastMethodCallError = "updateYesterday"
        assert client.lastMethodCallError == "updateYesterday"


class TestTimeTracking:
    def test_get_time_last_call_default(self, client):
        assert client.getTimeLastCall() is None

    def test_update_time_last_call(self, client):
        now = datetime.datetime.now()
        client.updateTimeLastCall(now)
        assert client.getTimeLastCall() == now

    def test_get_last_update_default(self, client):
        assert client.getLastUpdate() is None

    def test_update_last_update(self, client):
        client.updateLastUpdate("2024-01-01 12:00:00")
        assert client.getLastUpdate() == "2024-01-01 12:00:00"


class TestHoraire:
    def test_get_horaire_min(self, client):
        assert client.getHoraireMin() is not None
        assert isinstance(client.getHoraireMin(), int)

    def test_get_horaire_possible_default(self, client):
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "custom_components.myEnedis.myClientEnedis.datetime",
                MagicMock(datetime=datetime),
            )
            # Just check it returns bool
            result = client.getHorairePossible()
            assert isinstance(result, bool)


class TestGetCallPossible:
    def test_call_possible_when_never_called(self, client):
        # TimeLastCall is None, HorairePossible is True
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "custom_components.myEnedis.myClientEnedis.datetime",
                MagicMock(datetime=datetime),
            )
            result = client.getCallPossible()
            assert isinstance(result, bool)

    def test_get_last_call_hier_default(self, client):
        assert client.getLastCallHier() is not None
        assert isinstance(client.getLastCallHier(), bool)


class TestVersion:
    def test_version_initial(self, client):
        assert client.getVersion() == "0.0.0"

    def test_get_git_version(self, client):
        assert client.getGitVersion() is None

    def test_update_git_version(self, client):
        client.updateGitVersion()
        assert client.getGitVersion() is None


class TestDataJson:
    def test_set_data_json_default(self, client):
        client.setDataJsonDefault({"foo": "bar"})
        assert client.getDataJsonValue("foo") == "bar"

    def test_set_data_json_copy(self, client):
        original = {"a": 1}
        client.setDataJsonDefault(original)
        client.setDataJsonCopy()
        # After copy, values should persist
        assert client.getDataJsonValue("a") == 1
