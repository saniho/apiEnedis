"""Tests for sensorEnedis module - manageSensorState and helpers."""
from collections import defaultdict
from unittest.mock import MagicMock

import pytest

from custom_components.myEnedis.sensorEnedis import (
    _compute_evolution,
    manageSensorState,
)


class TestComputeEvolution:
    def test_computes_percentage(self):
        status = {}
        _compute_evolution(150, 100, "evolution", status)
        assert status["evolution"] == "50.000"

    def test_zero_when_previous_is_none(self):
        status = {}
        _compute_evolution(150, None, "evolution", status)
        assert status["evolution"] == 0

    def test_zero_when_previous_is_zero(self):
        status = {}
        _compute_evolution(150, 0, "evolution", status)
        assert status["evolution"] == 0

    def test_zero_when_current_is_none(self):
        status = {}
        _compute_evolution(None, 100, "evolution", status)
        assert status["evolution"] == 0

    def test_negative_evolution(self):
        status = {}
        _compute_evolution(50, 100, "evolution", status)
        assert status["evolution"] == "-50.000"


class TestManageSensorStateInit:
    def test_default_init_false(self):
        m = manageSensorState()
        assert m.getInit() is False

    def test_set_init_true(self):
        m = manageSensorState()
        m.setInit(True)
        assert m.getInit() is True

    def test_init_sets_attributes(self):
        mock_data = MagicMock()
        m = manageSensorState()
        m.init(mock_data, version="2.0.0")
        assert m._myDataEnedis is mock_data
        assert m.version == "2.0.0"
        assert m.getInit() is True


class TestManageSensorStateGetPDLID:
    def test_delegates_to_contract(self):
        mock_data = MagicMock()
        mock_data.contract.get_PDL_ID.return_value = "12345678901234"
        m = manageSensorState()
        m.init(mock_data)
        assert m.get_PDL_ID() == "12345678901234"


class TestGetStatusYesterdayCost:
    def test_returns_unavailable_when_no_hc_hp(self):
        mock_data = MagicMock()
        mock_data.contract is not None
        mock_data.getYesterdayHCHP().getHC.return_value = 0
        mock_data.getYesterdayHCHP().getHP.return_value = 0
        m = manageSensorState()
        m.init(mock_data, version="2.0.0")
        available, date, counts, state = m.getStatusYesterdayCost()
        assert available is False
        assert state == "unavailable"

    def test_returns_cost_when_data_available(self):
        mock_data = MagicMock()
        mock_data.contract is not None
        mock_data.getYesterdayHCHP().getHC.return_value = 5000
        mock_data.getYesterdayHCHP().getHP.return_value = 3000
        mock_data.getHCCost.return_value = 0.15
        mock_data.getHPCost.return_value = 0.20
        mock_data.getYesterday().getDateDeb.return_value = "2024-01-15"
        m = manageSensorState()
        m.init(mock_data, version="2.0.0")
        available, date, counts, state = m.getStatusYesterdayCost()
        assert available is True
        assert date == "2024-01-15"
        assert counts["version"] == "2.0.0"
        assert counts["yesterday_HC_cost"] == "0.750"
        assert counts["yesterday_HP_cost"] == "0.600"


class TestGetStatusEcoWatt:
    def test_returns_forecast(self):
        mock_data = MagicMock()
        mock_data.getTimeLastCall.return_value = "2024-01-15"
        mock_data.getEcoWatt().getValue.return_value = {}
        m = manageSensorState()
        m.init(mock_data, version="2.0.0")
        counts, state = m.getStatusEcoWatt()
        assert counts["version"] == "2.0.0"
        assert "forecast" in counts
        assert state != ""


class TestGetStatusTempo:
    def test_returns_today_color(self):
        mock_data = MagicMock()
        mock_data.getTimeLastCall.return_value = "2024-01-15"
        mock_data.getTempo().getValue.return_value = {}
        m = manageSensorState()
        m.init(mock_data, version="2.0.0")
        counts, state = m.getStatusTempo()
        assert counts["version"] == "2.0.0"
        assert "forecast" in counts


class TestGetStatus:
    def test_returns_defaults_when_no_time_last_call(self):
        mock_data = MagicMock()
        mock_data.getTimeLastCall.return_value = None
        mock_data.getGitVersion.return_value = "2.0.0"
        m = manageSensorState()
        m.init(mock_data, version="2.0.0")
        status, state = m.getStatus()
        assert status["version"] == "2.0.0"
        assert state == "unavailable"
