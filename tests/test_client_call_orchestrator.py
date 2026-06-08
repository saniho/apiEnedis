"""Tests for client_call_orchestrator functions."""
from unittest.mock import MagicMock, PropertyMock

import pytest

from custom_components.myEnedis.client_call_orchestrator import (
    call_consommation,
    call_ecowatt,
    call_production,
    call_tempo,
    do_update,
    get_call_possible,
)


@pytest.fixture
def client():
    c = MagicMock()
    c._forceCallJson = False
    c._niemeAppel = 0
    c._nbCall = 0
    c._PDL_ID = "test_pdl"
    c._myCalli = MagicMock()
    c._myCalli.getLastAnswer.return_value = None
    c.lastMethodCallError = ""
    c.lastMethodCall = ""
    c.contract.isLoaded = True
    c.contract.get_PDL_ID.return_value = "test_pdl"
    c.getVersion.return_value = "2.0.0"
    c.getStatusLastCall.return_value = True
    c.isConsommation.return_value = True
    c.isProduction.return_value = True
    c.getServiceEnedis.return_value = "enedisGateway"
    c.getHorairePossible.return_value = True
    c.getLastCallHier.return_value = True
    c.getTimeLastCall.return_value = None
    c.getDelayIsGoodAfterError.return_value = True
    c.getNbCall.return_value = 0
    return c


class TestGetCallPossible:
    def test_basic_true(self, client):
        assert get_call_possible(client) is True

    def test_horaire_impossible(self, client):
        client.getHorairePossible.return_value = False
        assert get_call_possible(client) is False

    def test_force_json_overrides(self, client):
        client.getHorairePossible.return_value = False
        client._forceCallJson = True
        assert get_call_possible(client) is True

    def test_trace_logging(self, client):
        result = get_call_possible(client, trace=True)
        assert result is True


class TestCallConsommation:
    def test_calls_all_updates_when_status_ok(self, client):
        call_consommation(client)
        assert client.updateYesterday.called
        assert client.updateCurrentWeek.called
        assert client.updateLastWeek.called
        assert client.updateLast7Days.called
        assert client.updateCurrentMonth.called
        assert client.updateLastMonth.called
        assert client.updateLastYear.called
        assert client.updateCurrentYear.called

    def test_skips_when_not_consommation(self, client):
        client.isConsommation.return_value = False
        call_consommation(client)
        assert client.updateYesterday.called is False

    def test_updates_time_and_status(self, client):
        call_consommation(client)
        assert client.updateTimeLastCall.called
        assert client.updateStatusLastCall.called

    def test_skips_time_when_force_json(self, client):
        client._forceCallJson = True
        call_consommation(client)
        assert client.updateTimeLastCall.called is False

    def test_retry_on_error(self, client):
        client.getStatusLastCall.return_value = False
        client.lastMethodCallError = "updateLastWeek"
        call_consommation(client)
        assert client.updateLastWeek.called
        assert client.updateYesterday.called is False


class TestCallProduction:
    def test_calls_update_when_production(self, client):
        call_production(client)
        assert client.updateYesterdayProduction.called

    def test_skips_when_not_production(self, client):
        client.isProduction.return_value = False
        call_production(client)
        assert client.updateYesterdayProduction.called is False

    def test_updates_time_and_status(self, client):
        call_production(client)
        assert client.updateTimeLastCall.called
        assert client.updateStatusLastCall.called


class TestCallEcoWatt:
    def test_calls_update_when_myelectricaldata_service(self, client):
        client.getServiceEnedis.return_value = "myElectricalData"
        call_ecowatt(client)
        assert client.updateEcoWatt.called

    def test_skips_when_wrong_service(self, client):
        client.getServiceEnedis.return_value = "enedisGateway"
        call_ecowatt(client)
        assert client.updateEcoWatt.called is False

    def test_updates_time_and_status(self, client):
        call_ecowatt(client)
        assert client.updateTimeLastCall.called
        assert client.updateStatusLastCall.called


class TestCallTempo:
    def test_calls_update_when_myelectricaldata_service(self, client):
        client.getServiceEnedis.return_value = "myElectricalData"
        call_tempo(client)
        assert client.updateTempo.called

    def test_skips_when_wrong_service(self, client):
        client.getServiceEnedis.return_value = "enedisGateway"
        call_tempo(client)
        assert client.updateTempo.called is False


class TestDoUpdate:
    def test_basic_update(self, client):
        do_update(client)
        assert client.updateYesterday.called
        assert client.updateLastUpdate.called

    def test_contract_not_loaded(self, client):
        client.contract.isLoaded = False
        do_update(client)
        assert client.setUpdateRealise.called
        assert client.updateYesterday.called is False

    def test_call_not_possible(self, client):
        client.getHorairePossible.return_value = False
        do_update(client)
        assert client.setUpdateRealise.called
        assert client.updateYesterday.called is False

    def test_resets_error_and_nb_call(self, client):
        do_update(client)
        assert client.updateErrorLastCall.called
        assert client._nbCall == 0

    def test_returns_true(self, client):
        assert do_update(client) is True
