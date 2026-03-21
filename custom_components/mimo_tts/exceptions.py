"""MiMo TTS client errors.

Maps to official error codes:
https://platform.xiaomimimo.com/#/docs/quick-start/error-codes
"""


class MimoAPIError(Exception):
    """Base class for all MiMo API errors."""


class MimoBadRequestError(MimoAPIError):
    """HTTP 400 — malformed request body, missing params, or invalid model."""


class MimoAuthError(MimoAPIError):
    """HTTP 401 — missing or invalid API key / Authorization header."""


class MimoForbiddenError(MimoAPIError):
    """HTTP 403 — region not supported or API key blocked by risk control."""


class MimoContentFilterError(MimoAPIError):
    """HTTP 421 — content moderation blocked the request."""


class MimoRateLimitError(MimoAPIError):
    """HTTP 429 — too many requests; implement backoff / reduce frequency."""


class MimoServerError(MimoAPIError):
    """HTTP 500 — internal server failure."""


class MimoServiceUnavailableError(MimoAPIError):
    """HTTP 503 — server overloaded."""
