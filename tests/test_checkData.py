"""Tests for myCheckData with unified error checking."""
import datetime
import json
import os

import pytest

from custom_components.myEnedis.exceptions import (
    EnedisApiError,
    EnedisAuthError,
    EnedisDataError,
)
from custom_components.myEnedis.myCheckData import myCheckData

JSON_DIR = os.path.join(os.path.dirname(__file__), "Json")


def load_json(filename):
    with open(os.path.join(JSON_DIR, filename)) as f:
        return json.load(f)


@pytest.fixture
def check():
    return myCheckData()


class TestCheckData:
    def test_check_data_valid(self, check):
        data = load_json("Yesterday/yesterday1.json")
        assert check.checkData(data) is True

    def test_check_data_no_meter_reading(self, check):
        assert check.checkData({}) is False

    def test_check_data_internal_error(self, check):
        data = {"error_code": "Internal Server error"}
        with pytest.raises(EnedisApiError, match="UNKERROR_001"):
            check.checkData(data)

    def test_check_data_unknown_error(self, check):
        data = {"error_code": "ADAM-ERR9999"}
        with pytest.raises(EnedisApiError, match="ADAM-ERR9999"):
            check.checkData(data)

    def test_check_data_500(self, check):
        data = {"error_code": 500}
        assert check.checkData(data) is False

    def test_check_data_adam_err0069(self, check):
        data = {"error_code": "ADAM-ERR0069"}
        assert check.checkData(data) is False

    def test_check_data_adam_dc_0008(self, check):
        data = {"error_code": "ADAM-DC-0008"}
        assert check.checkData(data) is False

    def test_check_data_user_alert(self, check):
        data = {"_error": "consent", "user_alert": True, "error": "ERR001", "description": "Consent missing"}
        with pytest.raises(EnedisAuthError):
            check.checkData(data)

    def test_check_data_no_data_found(self, check):
        data = {"error_code": "no_data_found"}
        with pytest.raises(EnedisDataError):
            check.checkData(data)


class TestCheckDataPeriod:
    def test_check_period_valid(self, check):
        data = load_json("Yesterday/yesterday1.json")
        assert check.checkDataPeriod(data) is True

    def test_check_period_no_data_found_returns_false(self, check):
        data = {"error_code": "no_data_found"}
        assert check.checkDataPeriod(data) is False

    def test_check_period_adam_err0123_returns_false(self, check):
        data = {"error_code": "ADAM-ERR0123"}
        assert check.checkDataPeriod(data) is False

    def test_check_period_adam_err0069_returns_false(self, check):
        data = {"error_code": "ADAM-ERR0069"}
        assert check.checkDataPeriod(data) is False

    def test_check_period_unknown_error(self, check):
        data = {"error_code": "ADAM-ERR9999"}
        with pytest.raises(EnedisApiError):
            check.checkDataPeriod(data)

    def test_check_period_no_meter_reading(self, check):
        assert check.checkDataPeriod({}) is False


class TestCheckDataEcoWatt:
    def test_check_ecowatt_valid(self, check):
        data = load_json("EcoWatt/updateEcoWatt.json")
        assert check.checkDataEcoWatt(data) is True

    def test_check_ecowatt_no_data(self, check):
        data = {"error_code": "no_data_found"}
        assert check.checkDataEcoWatt(data) is False

    def test_check_ecowatt_no_error(self, check):
        assert check.checkDataEcoWatt({}) is True


class TestCheckDataTempo:
    def test_check_tempo_valid(self, check):
        assert check.checkDataTempo({}) is True

    def test_check_tempo_no_data(self, check):
        data = {"error_code": "no_data_found"}
        assert check.checkDataTempo(data) is False

    def test_check_tempo_internal_error(self, check):
        data = {"error_code": "Internal Server error"}
        with pytest.raises(EnedisApiError):
            check.checkDataTempo(data)


class TestAnalyseValue:
    def test_analyse_value_valid(self, check):
        data = load_json("Yesterday/yesterday1.json")
        result = check.analyseValue(data)
        assert result == 42951

    def test_analyse_value_none(self, check):
        assert check.analyseValue(None) is None

    def test_analyse_value_no_meter_reading(self, check):
        assert check.analyseValue({}) is None

    def test_analyse_value_and_add_valid(self, check):
        data = load_json("Yesterday/yesterday1.json")
        result = check.analyseValueAndAdd(data)
        assert result == 42951

    def test_analyse_value_and_add_none(self, check):
        with pytest.raises(EnedisDataError):
            check.analyseValueAndAdd(None)


class TestAnalyseValueEcoWatt:
    def test_ecowatt_valid(self, check):
        data = load_json("EcoWatt/updateEcoWatt.json")
        result = check.analyseValueEcoWatt(data)
        assert isinstance(result, dict)

    def test_ecowatt_none(self, check):
        assert check.analyseValueEcoWatt(None) is None


class TestAnalyseValueEcoWattDetail:
    def test_with_detail_key(self, check):
        """When data has a 'detail' key, returns empty dict."""
        result = check.analyseValueEcoWatt({"detail": {"some": "data"}})
        assert result == {}

    def test_with_valid_data(self, check):
        data = load_json("EcoWatt/updateEcoWatt.json")
        result = check.analyseValueEcoWatt(data)
        assert isinstance(result, dict)
        assert len(result) > 0
        # Keys should be datetime objects
        for k in result:
            assert isinstance(k, datetime.datetime)
        # Values should have expected structure
        first_key = list(result.keys())[0]
        first_val = result[first_key]
        assert "value" in first_val
        assert "message" in first_val


class TestAnalyseValueTempo:
    def test_tempo_none(self, check):
        assert check.analyseValueTempo(None) is None

    def test_tempo_empty_dict(self, check):
        assert check.analyseValueTempo({}) == {}

    def test_tempo_with_data(self, check):
        result = check.analyseValueTempo({"2024-01-01": "BLUE", "2024-01-02": "RED"})
        assert len(result) == 2
        assert result[datetime.datetime(2024, 1, 1)] == "BLUE"
        assert result[datetime.datetime(2024, 1, 2)] == "RED"


class TestAnalyseValueAndMadeDico:
    def test_valid(self, check):
        data = load_json("Yesterday/yesterday1.json")
        result = check.analyseValueAndMadeDico(data)
        assert len(result) == 1
        assert result[0]["value"] == 42951
        assert result[0]["date"] == "2020-12-09"

    def test_none(self, check):
        with pytest.raises(EnedisDataError):
            check.analyseValueAndMadeDico(None)

    def test_empty(self, check):
        assert check.analyseValueAndMadeDico({}) == []
