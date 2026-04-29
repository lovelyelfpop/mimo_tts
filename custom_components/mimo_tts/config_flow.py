"""Config flow for Xiaomi MiMo TTS."""

from __future__ import annotations

import hashlib
import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_API_KEY,
    CONF_URL,
    DEFAULT_AUDIO_TAG_CONTROL,
    DEFAULT_CHAT_COMPLETIONS_URL,
    DEFAULT_MODEL,
    DEFAULT_NATURAL_LANGUAGE_CONTROL,
    DOMAIN,
    LANG_EN_MIA,
    apply_audio_tag_control,
    voice_for_language,
)
from .exceptions import (
    MimoAPIError,
    MimoAuthError,
    MimoBadRequestError,
    MimoContentFilterError,
    MimoForbiddenError,
    MimoRateLimitError,
    MimoServerError,
    MimoServiceUnavailableError,
)
from .mimo_client import MimoTTSClient

_LOGGER = logging.getLogger(__name__)


class InvalidAuth(HomeAssistantError):
    """Invalid API credentials."""


class CannotConnect(HomeAssistantError):
    """Cannot reach API."""


class BadRequest(HomeAssistantError):
    """Malformed request."""


class Forbidden(HomeAssistantError):
    """Access denied — region or risk-control block."""


class ContentFiltered(HomeAssistantError):
    """Content blocked by moderation."""


class RateLimited(HomeAssistantError):
    """Too many requests."""


class ServerFailure(HomeAssistantError):
    """Server-side error (500 / 503)."""


def _entry_data_schema(defaults: dict[str, Any]) -> vol.Schema:
    url_default = defaults.get(CONF_URL) or DEFAULT_CHAT_COMPLETIONS_URL
    return vol.Schema(
        {
            vol.Required(CONF_API_KEY, default=defaults.get(CONF_API_KEY, "")): str,
            vol.Optional(CONF_URL, default=url_default): str,
        }
    )


async def _validate_speech(data: dict[str, Any]) -> None:
    """Try a short synthesis request (English voice; language is mapped at runtime)."""
    url = (data.get(CONF_URL) or "").strip() or DEFAULT_CHAT_COMPLETIONS_URL

    client = MimoTTSClient(
        api_key=data[CONF_API_KEY],
        url=url,
    )
    _LOGGER.debug("MiMo TTS setup validation: url=%s", url)

    try:
        async with aiohttp.ClientSession() as session:
            await client.async_synthesize(
                session,
                apply_audio_tag_control("Hi", DEFAULT_AUDIO_TAG_CONTROL),
                voice=voice_for_language(LANG_EN_MIA),
                instruction=DEFAULT_NATURAL_LANGUAGE_CONTROL,
            )
    except MimoAuthError as err:
        _LOGGER.error("MiMo TTS setup: authentication failed — %s", err)
        raise InvalidAuth from err
    except MimoBadRequestError as err:
        _LOGGER.error("MiMo TTS setup: bad request — %s", err)
        raise BadRequest(str(err)) from err
    except MimoForbiddenError as err:
        _LOGGER.error("MiMo TTS setup: access denied — %s", err)
        raise Forbidden(str(err)) from err
    except MimoContentFilterError as err:
        _LOGGER.error("MiMo TTS setup: content filtered — %s", err)
        raise ContentFiltered(str(err)) from err
    except MimoRateLimitError as err:
        _LOGGER.error("MiMo TTS setup: rate limited — %s", err)
        raise RateLimited(str(err)) from err
    except (MimoServerError, MimoServiceUnavailableError) as err:
        _LOGGER.error("MiMo TTS setup: server error — %s", err)
        raise ServerFailure(str(err)) from err
    except MimoAPIError as err:
        _LOGGER.error("MiMo TTS setup: API error — %s", err)
        raise CannotConnect(str(err)) from err
    except (aiohttp.ClientError, TimeoutError, OSError) as err:
        _LOGGER.error(
            "MiMo TTS setup: connection error — %s",
            err,
            exc_info=True,
        )
        raise CannotConnect(str(err)) from err


class MimoTTSConfigFlow(ConfigFlow, domain=DOMAIN):
    """MiMo TTS config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """First step: API and speech settings."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await _validate_speech(user_input)
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except BadRequest:
                errors["base"] = "bad_request"
            except Forbidden:
                errors["base"] = "forbidden"
            except ContentFiltered:
                errors["base"] = "content_filtered"
            except RateLimited:
                errors["base"] = "rate_limited"
            except ServerFailure:
                errors["base"] = "server_error"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("MiMo TTS setup: unexpected error during validation")
                errors["base"] = "unknown"
            else:
                uid_src = (
                    f"{user_input[CONF_API_KEY]}:"
                    f"{user_input.get(CONF_URL, DEFAULT_CHAT_COMPLETIONS_URL)}"
                )
                uid = hashlib.sha256(uid_src.encode()).hexdigest()[:16]
                await self.async_set_unique_id(f"mimo_tts_{uid}")
                self._abort_if_unique_id_configured()
                clean = {
                    CONF_API_KEY: user_input[CONF_API_KEY],
                    CONF_URL: (
                        user_input.get(CONF_URL) or ""
                    ).strip()
                    or DEFAULT_CHAT_COMPLETIONS_URL,
                }
                return self.async_create_entry(
                    title=DEFAULT_MODEL,
                    data=clean,
                )

        defaults: dict[str, Any] = user_input if user_input else {}
        return self.async_show_form(
            step_id="user",
            data_schema=_entry_data_schema(defaults),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Reconfigure API key and speech URL."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            merged = {**entry.data, **user_input}
            try:
                await _validate_speech(merged)
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except BadRequest:
                errors["base"] = "bad_request"
            except Forbidden:
                errors["base"] = "forbidden"
            except ContentFiltered:
                errors["base"] = "content_filtered"
            except RateLimited:
                errors["base"] = "rate_limited"
            except ServerFailure:
                errors["base"] = "server_error"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("MiMo TTS reconfigure: unexpected error")
                errors["base"] = "unknown"
            else:
                clean = {
                    CONF_API_KEY: merged[CONF_API_KEY],
                    CONF_URL: (merged.get(CONF_URL) or "").strip()
                    or DEFAULT_CHAT_COMPLETIONS_URL,
                }
                self.hass.config_entries.async_update_entry(entry, data=clean)
                return self.async_abort(reason="reconfigure_successful")

        defaults = dict(entry.data)
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_entry_data_schema(defaults),
            errors=errors,
        )
