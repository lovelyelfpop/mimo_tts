"""Text-to-speech platform for Xiaomi MiMo."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import aiohttp

from homeassistant.components.tts import TextToSpeechEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_API_KEY,
    CONF_URL,
    CONF_STYLE,
    DEFAULT_CHAT_COMPLETIONS_URL,
    DEFAULT_MODEL,
    DEVICE_CONFIGURATION_URL,
    DEVICE_MODEL,
    DOMAIN,
    MANUFACTURER,
    voice_for_language,
)
from .exceptions import (
    MimoAPIError,
    MimoAuthError,
    MimoContentFilterError,
    MimoRateLimitError,
)
from .mimo_client import MimoTTSClient

_LOGGER = logging.getLogger(__name__)

_STYLE_TAG_RE = re.compile(r"<style>.*?</style>", re.DOTALL)

# Only English and Chinese; voice is derived via voice_for_language().
SUPPORTED_LANGUAGES = ["en", "zh"]


def _get_url(data: dict[str, Any]) -> str:
    return (data.get(CONF_URL) or "").strip() or DEFAULT_CHAT_COMPLETIONS_URL


def _apply_default_style(message: str, default_style: str) -> str:
    """Prepend <style> tag unless the message already contains one."""
    if not default_style:
        return message
    if _STYLE_TAG_RE.search(message):
        return message
    return f"<style>{default_style}</style>{message}"


def _integration_sw_version() -> str:
    """Match manifest.json version for device_info sw_version."""
    try:
        manifest = Path(__file__).parent / "manifest.json"
        return str(json.loads(manifest.read_text(encoding="utf-8"))["version"])
    except (OSError, KeyError, json.JSONDecodeError, ValueError, TypeError):
        return "unknown"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MiMo TTS entity."""
    sw_version = await hass.async_add_executor_job(_integration_sw_version)
    async_add_entities([MimoTTSEntity(hass, config_entry, sw_version)], True)


class MimoTTSEntity(TextToSpeechEntity):
    """MiMo TTS via chat.completions + audio (WAV)."""

    # Explicit name avoids UndefinedType in HA TTS media browser (sorted by title).
    _attr_has_entity_name = False
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, sw_version: str) -> None:
        self.hass = hass
        self._entry = config_entry
        self._attr_unique_id = config_entry.unique_id

        style = (config_entry.data.get(CONF_STYLE) or "").strip()
        self._attr_name = f"{DEFAULT_MODEL}-{style}" if style else DEFAULT_MODEL

        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": f"{DEFAULT_MODEL}-{style}" if style else DEFAULT_MODEL,
            "manufacturer": MANUFACTURER,
            "model": DEVICE_MODEL,
            "configuration_url": DEVICE_CONFIGURATION_URL,
            "sw_version": sw_version,
        }

    def _client(self) -> MimoTTSClient:
        data = self._entry.data
        return MimoTTSClient(
            api_key=data[CONF_API_KEY],
            url=_get_url(data),
        )

    @property
    def default_language(self) -> str:
        return "en"

    @property
    def supported_languages(self) -> list[str]:
        return SUPPORTED_LANGUAGES

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        style = (self._entry.data.get(CONF_STYLE) or "").strip()
        return {"style": style} if style else {}

    async def async_config_entry_updated(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Refresh when the user reconfigures."""
        self._entry = entry
        style = (entry.data.get(CONF_STYLE) or "").strip()
        self._attr_name = f"{DEFAULT_MODEL}-{style}" if style else DEFAULT_MODEL
        self.async_write_ha_state()

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any] | None = None
    ) -> tuple[str | None, bytes | None]:
        """Return WAV audio bytes; voice follows HA language (zh vs en)."""
        voice = voice_for_language(language)
        default_style = (self._entry.data.get(CONF_STYLE) or "").strip()
        message = _apply_default_style(message, default_style)

        client = self._client()
        try:
            async with aiohttp.ClientSession() as session:
                audio, ext = await client.async_synthesize(
                    session,
                    message,
                    voice=voice,
                )
        except MimoAuthError as err:
            _LOGGER.error("MiMo TTS auth error — check API key: %s", err)
            return None, None
        except MimoContentFilterError as err:
            _LOGGER.warning("MiMo TTS content blocked by moderation: %s", err)
            return None, None
        except MimoRateLimitError as err:
            _LOGGER.warning("MiMo TTS rate limited — retry later: %s", err)
            return None, None
        except MimoAPIError as err:
            _LOGGER.error("MiMo TTS synthesis failed: %s", err)
            return None, None
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("MiMo TTS unexpected error: %s", err)
            return None, None

        return ext, audio
