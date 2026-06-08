"""Tests for custom exceptions."""
from custom_components.myEnedis.exceptions import (
    EnedisError,
    EnedisApiError,
    EnedisAuthError,
    EnedisDataError,
)


def test_exception_hierarchy():
    assert issubclass(EnedisApiError, EnedisError)
    assert issubclass(EnedisAuthError, EnedisError)
    assert issubclass(EnedisDataError, EnedisError)
    assert issubclass(EnedisError, Exception)


def test_enedis_api_error():
    exc = EnedisApiError("UNKERROR_001")
    assert str(exc) == "UNKERROR_001"
    assert isinstance(exc, EnedisError)


def test_enedis_auth_error():
    exc = EnedisAuthError("token_refresh_401", "Token expiré")
    assert exc.args[0] == "token_refresh_401"
    assert exc.args[1] == "Token expiré"
    assert isinstance(exc, EnedisError)


def test_enedis_data_error():
    exc = EnedisDataError("Collecte de données non activée")
    assert "Collecte" in str(exc)
    assert isinstance(exc, EnedisError)


def test_exceptions_caught_by_base():
    errors = [
        EnedisApiError("test"),
        EnedisAuthError("test"),
        EnedisDataError("test"),
    ]
    for exc in errors:
        assert isinstance(exc, EnedisError)
        assert isinstance(exc, Exception)
