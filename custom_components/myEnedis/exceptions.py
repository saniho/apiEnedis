"""Custom exceptions for myEnedis."""


class EnedisError(Exception):
    """Base exception for myEnedis."""


class EnedisApiError(EnedisError):
    """API returned an error."""


class EnedisAuthError(EnedisError):
    """Authentication or consent error."""


class EnedisDataError(EnedisError):
    """No data available."""


class EnedisQuotaError(EnedisApiError):
    """API quota exceeded (50 calls/day)."""


