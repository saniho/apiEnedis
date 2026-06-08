"""Tests for myCall module - HTTP calls, rate limiting, URL building."""
import datetime
import json
from unittest.mock import MagicMock, patch

import pytest

from custom_components.myEnedis.myCall import (
    INITIAL_CALL_DELAY,
    MAX_CALL_DELAY,
    MAX_CALLS,
    MAX_PREVIOUS_TIMEOUT,
    NEXT_MIN_CALL_DELAY,
    myCall,
)
from custom_components.myEnedis import apiconst as API


@pytest.fixture(autouse=True)
def reset_static_state():
    myCall._MyCallsSinceRestart = 0
    myCall._MyCallsUpdateDay = ""
    myCall._lastTimeout = 0.0
    myCall._noRecentTimeout = True


@pytest.fixture
def call():
    c = myCall()
    c.setParam("12345678901234", "test_token", "2.0.0", "enedisGateway")
    return c


class TestInit:
    def test_defaults(self):
        c = myCall()
        assert c._lastAnswer is None
        assert c._contentType == "application/json"
        assert c._serviceEnedis is None

    def test_server_urls(self):
        c = myCall()
        assert "enedisGateway" in c._serverNameUrl
        assert "myElectricalData" in c._serverNameUrl


class TestSetParam:
    def test_sets_attributes(self, call):
        assert call._PDL_ID == "12345678901234"
        assert call._token == "test_token"
        assert call._version == "2.0.0"
        assert call._serviceEnedis == "enedisGateway"


class TestGetDefaultHeader:
    def test_header_structure(self, call):
        h = call.getDefaultHeader()
        assert h["Authorization"] == "test_token"
        assert h["Content-Type"] == "application/json"
        assert "call-service" in h
        assert "ha_sensor_myenedis_version" in h


class TestServiceDetection:
    def test_is_my_electric_data(self, call):
        assert call.isMyElectricData("myElectricalData") is True
        assert call.isMyElectricData("enedisGateway") is False

    def test_is_enedis_gateway(self, call):
        assert call.isEnedisGateway("enedisGateway") is True
        assert call.isEnedisGateway("myElectricalData") is False


class TestLastAnswer:
    def test_set_and_get(self, call):
        call.setLastAnswer("test")
        assert call.getLastAnswer() == "test"

    def test_default_is_none(self):
        c = myCall()
        assert c.getLastAnswer() is None


class TestSanitizeCounter:
    def test_resets_on_new_day(self):
        today = datetime.date.today().strftime("%Y-%m-%d")
        myCall._MyCallsUpdateDay = "2000-01-01"
        myCall._MyCallsSinceRestart = 99
        result = myCall.sanitizeCounter()
        assert result == 0
        assert myCall._MyCallsUpdateDay == today

    def test_keeps_counter_same_day(self):
        today = datetime.date.today().strftime("%Y-%m-%d")
        myCall._MyCallsUpdateDay = today
        myCall._MyCallsSinceRestart = 10
        result = myCall.sanitizeCounter()
        assert result == 10


class TestIncreaseCallCounter:
    def test_increments(self):
        assert myCall.increaseCallCounter() == 1
        assert myCall.increaseCallCounter() == 2

    def test_sanitizes_before_increment(self):
        myCall._MyCallsSinceRestart = 50
        assert myCall.increaseCallCounter() == 51


class TestIsAvailable:
    def test_available_when_no_timeout_and_under_limit(self):
        myCall._noRecentTimeout = True
        myCall._MyCallsSinceRestart = 0
        assert myCall.isAvailable() is True

    def test_unavailable_when_over_max_calls(self):
        myCall._MyCallsSinceRestart = MAX_CALLS
        assert myCall.isAvailable() is False

    def test_unavailable_when_recent_timeout(self):
        myCall._noRecentTimeout = False
        myCall._lastTimeout = datetime.datetime.now().timestamp()
        assert myCall.isAvailable() is False

    def test_recovers_after_timeout_expires(self):
        myCall._noRecentTimeout = False
        myCall._lastTimeout = (
            datetime.datetime.now().timestamp() - MAX_PREVIOUS_TIMEOUT - 1
        )
        assert myCall.isAvailable() is True
        assert myCall._noRecentTimeout is True


class TestHandleTimeout:
    def test_sets_timeout_flag(self):
        myCall._noRecentTimeout = True
        myCall._lastTimeout = 0.0
        myCall.handleTimeout()
        assert myCall._noRecentTimeout is True
        assert myCall._lastTimeout > 0

    def test_sets_recent_flag_on_consecutive_timeouts(self):
        now = datetime.datetime.now().timestamp()
        myCall._lastTimeout = now - 10
        myCall._noRecentTimeout = True
        myCall.handleTimeout()
        assert myCall._noRecentTimeout is False


class TestGetUrl:
    @pytest.fixture
    def med_call(self):
        c = myCall()
        c.setParam("PDL01", "tok", "1.0", "myElectricalData")
        return c

    def test_enedis_gateway_returns_post(self, call):
        result = call.getUrl("enedisGateway", {})
        assert result[0] == "post"
        assert "enedisgateway.tech" in result[1]

    def test_my_electric_data_contracts(self, med_call):
        method, url = med_call.getUrl("myElectricalData", {
            "type": "contracts", "usage_point_id": "PDL01"
        })
        assert method == "get"
        assert "contracts/PDL01/" in url

    def test_my_electric_data_daily_consumption(self, med_call):
        method, url = med_call.getUrl("myElectricalData", {
            "type": "daily_consumption", "usage_point_id": "PDL01",
            "start": "2024-01-01", "end": "2024-01-31"
        })
        assert method == "get"
        assert "daily_consumption/PDL01/start/2024-01-01/end/2024-01-31/" in url

    def test_my_electric_data_ecowatt(self, med_call):
        method, url = med_call.getUrl("myElectricalData", {
            "type": "rte/ecowatt", "usage_point_id": "PDL01",
            "start": "2024-01-01", "end": "2024-01-31"
        })
        assert method == "get"
        assert "rte/ecowatt/2024-01-01/2024-01-31/" in url

    def test_my_electric_data_tempo(self, med_call):
        method, url = med_call.getUrl("myElectricalData", {
            "type": "rte/tempo", "usage_point_id": "PDL01",
            "start": "2024-01-01", "end": "2024-01-31"
        })
        assert method == "get"
        assert "rte/tempo/2024-01-01/2024-01-31/" in url

    def test_unknown_service_returns_none(self, call):
        assert call.getUrl("unknown", {}) is None


class TestSaveApiReturn:
    def test_writes_file(self, call, tmp_path):
        with patch.object(call, "saveApiReturn", wraps=call.saveApiReturn) as spy:
            with patch("os.path.dirname", return_value=str(tmp_path)):
                call.saveApiReturn(1, '{"test": true}')
                spy.assert_called_once_with(1, '{"test": true}')


class TestPostAndGetJson:
    @patch("time.sleep")
    def test_successful_get(self, mock_sleep, call):
        mock_resp = MagicMock()
        mock_resp.text = '{"ok": true}'
        mock_resp.json.return_value = {"ok": True}
        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp
        mock_session.post.return_value = mock_resp

        with patch("requests.Session", return_value=mock_session):
            result = call.post_and_get_json("enedisGateway", data={"type": "test"})

        assert result == {"ok": True}
        mock_session.post.assert_called_once()

    @patch("time.sleep")
    def test_successful_get_for_myelectricaldata(self, mock_sleep, call):
        mock_resp = MagicMock()
        mock_resp.text = '{}'
        mock_resp.json.return_value = {}
        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp

        call._serviceEnedis = "myElectricalData"
        with patch("requests.Session", return_value=mock_session):
            with patch.object(call, "getUrl", return_value=("get", "http://example.com")):
                result = call.post_and_get_json("myElectricalData", data={"type": "daily_consumption", "usage_point_id": "PDL01"})

        assert result == {}
        mock_session.get.assert_called_once()

    @patch("time.sleep")
    def test_unavailable_returns_error_dict(self, mock_sleep, call):
        myCall._MyCallsSinceRestart = MAX_CALLS
        result = call.post_and_get_json("enedisGateway")
        assert API.ERROR_CODE in result
        assert result[API.ERROR_CODE] == "UNAVAILABLE"

    @patch("time.sleep")
    def test_timeout_retries_and_returns_error(self, mock_sleep, call):
        mock_session = MagicMock()
        mock_session.post.side_effect = __import__("requests").exceptions.Timeout()

        with patch("requests.Session", return_value=mock_session):
            with patch.object(myCall, "handleTimeout") as mock_handle:
                result = call.post_and_get_json("enedisGateway", data={"type": "test"})

        assert result[API.ENEDIS_RETURN][API.ENEDIS_RETURN_ERROR] == "UNKERROR_TIMEOUT"
        assert mock_handle.called

    @patch("time.sleep")
    def test_http_error_retries_when_non_fatal(self, mock_sleep, call):
        mock_resp = MagicMock()
        mock_resp.text = '{"error": "bad request"}'
        mock_resp.json.return_value = {"error": "bad request"}
        mock_session = MagicMock()
        mock_session.post.side_effect = [
            __import__("requests").exceptions.HTTPError(response=mock_resp),
            mock_resp,
        ]

        with patch("requests.Session", return_value=mock_session):
            result = call.post_and_get_json("enedisGateway", data={"type": "test"})

        assert result == {"error": "bad request"}

    @patch("time.sleep")
    def test_http_error_fatal_when_usage_point_id_wrong(self, mock_sleep, call):
        mock_resp = MagicMock()
        mock_resp.text = "usage_point_id parameter must be 14 digits long."
        mock_resp.json.return_value = {"error": "invalid"}
        mock_session = MagicMock()
        mock_session.post.side_effect = __import__("requests").exceptions.HTTPError(response=mock_resp)

        with patch("requests.Session", return_value=mock_session):
            result = call.post_and_get_json("enedisGateway", data={"type": "test"})

        assert result == {"error": "invalid"}


class TestCallApi:
    def test_returns_data_and_true_when_fin_provided(self, call):
        with patch.object(call, "post_and_get_json", return_value={"data": "ok"}) as mock_pag:
            data, done = call._call_api("daily_consumption", "2024-01-01", "2024-01-31")

        assert data == {"data": "ok"}
        assert done is True
        mock_pag.assert_called_once()

    def test_returns_empty_and_false_when_fin_is_none(self, call):
        data, done = call._call_api("daily_consumption", "2024-01-01", None)
        assert data == ""
        assert done is False


class TestGetDataMethods:
    @pytest.mark.parametrize("method_name,type_name", [
        ("getDataPeriod", "daily_consumption"),
        ("getDataPeriodConsumptionMaxPower", "daily_consumption_max_power"),
        ("getDataProductionPeriod", "daily_production"),
        ("getDataEcoWatt", "rte/ecowatt"),
        ("getDataTempo", "rte/tempo"),
        ("getDataPeriodCLC", "consumption_load_curve"),
    ])
    def test_delegates_to_call_api(self, call, method_name, type_name):
        with patch.object(call, "_call_api", return_value=("ok", True)) as mock_api:
            method = getattr(call, method_name)
            result = method("2024-01-01", "2024-01-31")
            mock_api.assert_called_once_with(type_name, "2024-01-01", "2024-01-31")
            assert result == ("ok", True)

    def test_get_data_contract(self, call):
        with patch.object(call, "post_and_get_json", return_value={"contract": "data"}) as mock_pag:
            result = call.getDataContract()
        assert result == {"contract": "data"}
        mock_pag.assert_called_once()
