"""Tests for myContrat - no HA dependency."""
import pytest

from custom_components.myEnedis.myContrat import myContrat
from custom_components.myEnedis.exceptions import EnedisApiError, EnedisAuthError


@pytest.fixture
def contract():
    return myContrat(None, "myToken", "myPDL", "1.0.0", True, None)


class TestInit:
    def test_default_state(self, contract):
        assert contract.get_PDL_ID() == "myPDL"
        assert contract.get_token() == "myToken"
        assert contract.get_version() == "1.0.0"
        assert contract.isLoaded is False
        assert contract.getsubscribed_power() == "???"
        assert contract.getoffpeak_hours() == ()
        assert contract.getHeuresCreuses() is None
        assert contract.getLastActivationDate() is None
        assert contract.getUsagePointStatus() is None
        assert contract.getTypePDL() is None

    def test_heures_creuses_on(self):
        c = myContrat(None, "t", "p", "1.0.0", True, [["00:00", "06:00"]])
        assert c.getHeuresCreuses() == [["00:00", "06:00"]]

    def test_heures_creuses_off(self):
        c = myContrat(None, "t", "p", "1.0.0", False, None)
        c.updateHCHP()
        assert c.getHeuresCreuses() == []


class TestUpdateHCHP:
    def test_heures_creuses_on_with_offpeak(self, contract):
        contract._contract["offpeak_hours"] = "HC (23H30-7H30)"
        contract.updateHCHP()
        assert contract.getHeuresCreuses() == [["23:30", "23:59"], ["00:00", "07:30"]]

    def test_heures_creuses_on_without_offpeak(self, contract):
        contract.updateHCHP()
        assert contract.getHeuresCreuses() == []

    def test_preserve_custom_hours(self, contract):
        custom = [["22:00", "06:00"]]
        c = myContrat(None, "t", "p", "1.0.0", True, custom)
        c._contract["offpeak_hours"] = "HC (23H30-7H30)"
        c.updateHCHP()
        assert c.getHeuresCreuses() == custom


class TestCompareDate:
    def test_min_compare_before_contract(self, contract):
        contract._contract["last_activation_date"] = "2023-06-01"
        assert contract.minCompareDateContract("2023-01-01") == "2023-06-01"

    def test_min_compare_after_contract(self, contract):
        contract._contract["last_activation_date"] = "2023-01-01"
        assert contract.minCompareDateContract("2023-06-01") == "2023-06-01"

    def test_min_compare_no_activation(self, contract):
        assert contract.minCompareDateContract("2023-06-01") == "2023-06-01"

    def test_max_compare_before_contract(self, contract):
        contract._contract["last_activation_date"] = "2023-06-01"
        assert contract.maxCompareDateContract("2023-01-01") is None

    def test_max_compare_after_contract(self, contract):
        contract._contract["last_activation_date"] = "2023-01-01"
        assert contract.maxCompareDateContract("2023-06-01") == "2023-06-01"

    def test_max_compare_no_activation(self, contract):
        assert contract.maxCompareDateContract("2023-06-01") is None


class TestCleanOffpeak:
    def test_standard_format(self, contract):
        result = contract.getcleanoffpeak_hours("HC (23H30-7H30)")
        assert result == [["23:30", "23:59"], ["00:00", "07:30"]]

    def test_multi_slot(self, contract):
        result = contract.getcleanoffpeak_hours("HC (12H00-14H00;23H30-7H30)")
        assert result == [["12:00", "14:00"], ["23:30", "23:59"], ["00:00", "07:30"]]

    def test_none_input(self, contract):
        assert contract.getcleanoffpeak_hours(None) == []

    def test_empty_string(self, contract):
        assert contract.getcleanoffpeak_hours("") == []

    def test_list_passthrough(self, contract):
        assert contract.getcleanoffpeak_hours([["00:00", "06:00"]]) == [
            ["00:00", "06:00"]
        ]


class TestGetHCHP:
    def test_heure_pleine(self, contract):
        contract._heuresCreuses = [["00:00", "06:00"]]
        assert contract._getHCHPfromHour("14:00") is True

    def test_heure_creuse(self, contract):
        contract._heuresCreuses = [["00:00", "06:00"]]
        assert contract._getHCHPfromHour("03:00") is False

    def test_no_heures_creuses(self, contract):
        contract._heuresCreuses = None
        assert contract._getHCHPfromHour("03:00") is True


class TestCheckDataContract:
    def test_unkerror_001_returns_false(self, contract):
        assert contract._myContrat__checkDataContract(
            {"error_code": "UNKERROR_001"}
        ) is False

    def test_other_error_raises(self, contract):
        with pytest.raises(EnedisApiError):
            contract._myContrat__checkDataContract({"error_code": "ADAM-ERR9999"})

    def test_token_refresh_raises_auth(self, contract):
        with pytest.raises(EnedisAuthError):
            contract._myContrat__checkDataContract(
                {"error": "token_refresh_401", "description": "Token expired"}
            )

    def test_success_returns_true(self, contract):
        assert contract._myContrat__checkDataContract({"status": "ok"}) is True


class TestAnalyseValueContract:
    def test_matching_pdl(self, contract):
        data = {
            "customer": {
                "usage_points": [
                    {
                        "usage_point": {"usage_point_id": "myPDL"},
                        "contracts": {
                            "subscribed_power": "9 kVA",
                            "offpeak_hours": "HC (23H30-7H30)",
                            "last_activation_date": "2007-07-06T00:00:00Z",
                        },
                    }
                ]
            }
        }
        result = contract._myContrat__analyseValueContract(data)
        assert result["is_loaded"] is True
        assert result["subscribed_power"] == "9 kVA"
        assert result["last_activation_date"] == "2007-07-06"
        assert result["usage_point_status"] == "myPDL"
        assert _consommation in result["mode_PDL"]
        assert _production in result["mode_PDL"]

    def test_non_matching_pdl(self, contract):
        data = {
            "customer": {
                "usage_points": [
                    {
                        "usage_point": {"usage_point_id": "otherPDL"},
                        "contracts": {},
                    }
                ]
            }
        }
        assert contract._myContrat__analyseValueContract(data) is None

    def test_no_customer_key(self, contract):
        assert contract._myContrat__analyseValueContract({}) is None


class TestSetContract:
    def test_with_dict(self, contract):
        contract._myContrat__setContract({"is_loaded": True, "subscribed_power": "6 kVA"})
        assert contract.isLoaded is True
        assert contract.getsubscribed_power() == "6 kVA"

    def test_with_none_resets_to_default(self, contract):
        contract._myContrat__setContract({"is_loaded": True})
        contract._myContrat__setContract(None)
        assert contract.isLoaded is False
        assert contract.getsubscribed_power() == "???"

    def test_with_non_dict_resets_to_default(self, contract):
        contract._myContrat__setContract({"is_loaded": True})
        contract._myContrat__setContract("invalid")
        assert contract.isLoaded is False


# Need constants for mode_PDL check
from custom_components.myEnedis.const import _consommation, _production
