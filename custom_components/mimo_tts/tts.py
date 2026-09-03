"""Text-to-speech platform for Xiaomi MiMo."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import aiohttp

from homeassistant.components.tts import ATTR_VOICE, Voice, TextToSpeechEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_API_KEY,
    CONF_URL,
    CONF_AUDIO_TAG_CONTROL,
    CONF_NATURAL_LANGUAGE_CONTROL,
    DEFAULT_AUDIO_TAG_CONTROL,
    DEFAULT_CHAT_COMPLETIONS_URL,
    DEFAULT_MODEL,
    DEFAULT_NATURAL_LANGUAGE_CONTROL,
    DEVICE_CONFIGURATION_URL,
    DEVICE_MODEL,
    DOMAIN,
    MANUFACTURER,
    OPTION_AUDIO_TAG_CONTROL,
    OPTION_NATURAL_LANGUAGE_CONTROL,
    SUPPORTED_LANGUAGES,
    apply_audio_tag_control,
    voice_for_language,
    voices_for_language,
)
from .exceptions import (
    MimoAPIError,
    MimoAuthError,
    MimoContentFilterError,
    MimoRateLimitError,
)
from .mimo_client import MimoTTSClient

_LOGGER = logging.getLogger(__name__)

def _get_url(data: dict[str, Any]) -> str:
    return (data.get(CONF_URL) or "").strip() or DEFAULT_CHAT_COMPLETIONS_URL


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

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        sw_version: str,
    ) -> None:
        self.hass = hass
        self._entry = config_entry
        self._attr_unique_id = config_entry.unique_id

        self._attr_name = DEFAULT_MODEL

        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": DEFAULT_MODEL,
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
        return SUPPORTED_LANGUAGES[0]

    @property
    def supported_languages(self) -> list[str]:
        return SUPPORTED_LANGUAGES

    @property
    def supported_options(self) -> list[str]:
        return [ATTR_VOICE, OPTION_NATURAL_LANGUAGE_CONTROL, OPTION_AUDIO_TAG_CONTROL]

    @callback
    def async_get_supported_voices(self, language: str) -> list[Voice] | None:
        """Return the MiMo built-in voices available for a language."""
        voices = voices_for_language(language)
        if voices is None:
            return None
        return [Voice(voice_id, voice_id) for voice_id in voices]

    @property
    def default_options(self) -> dict[str, str]:
        return {
            OPTION_NATURAL_LANGUAGE_CONTROL: self._get_natural_language_control(),
            OPTION_AUDIO_TAG_CONTROL: self._get_audio_tag_control(),
        }

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "natural_language_control": self._get_natural_language_control(),
            "audio_tag_control": self._get_audio_tag_control(),
        }

    def _get_natural_language_control(self) -> str:
        return (
            self._entry.data.get(CONF_NATURAL_LANGUAGE_CONTROL)
            or DEFAULT_NATURAL_LANGUAGE_CONTROL
        ).strip()

    def _get_audio_tag_control(self) -> str:
        return (
            self._entry.data.get(CONF_AUDIO_TAG_CONTROL) or DEFAULT_AUDIO_TAG_CONTROL
        ).strip()

    async def async_config_entry_updated(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Refresh when the user reconfigures."""
        self._entry = entry
        self._attr_name = DEFAULT_MODEL
        self.async_write_ha_state()

    def _get_voice(self, language: str, options: dict[str, Any]) -> str:
        """Resolve the MiMo voice id from an options `voice` key or language."""
        voice = str(options.get(ATTR_VOICE) or "").strip()
        available = voices_for_language(language)
        if voice and available is not None and voice in available:
            return voice
        return voice_for_language(language)

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any] | None = None
    ) -> tuple[str | None, bytes | None]:
        """Return WAV audio bytes; voice chosen from HA language / voice option."""
        options = options or {}
        voice = self._get_voice(language, options)
        natural_language_control = str(
            options.get(OPTION_NATURAL_LANGUAGE_CONTROL)
            or self._get_natural_language_control()
        ).strip()
        audio_tag_control = str(
            options.get(OPTION_AUDIO_TAG_CONTROL) or self._get_audio_tag_control()
        ).strip()
        message = apply_audio_tag_control(message, audio_tag_control)

        client = self._client()
        try:
            async with aiohttp.ClientSession() as session:
                audio, ext = await client.async_synthesize(
                    session,
                    message,
                    voice=voice,
                    instruction=natural_language_control or None,
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
