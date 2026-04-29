"""Editable text entities for Xiaomi MiMo TTS."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_AUDIO_TAG_CONTROL,
    CONF_NATURAL_LANGUAGE_CONTROL,
    DEFAULT_AUDIO_TAG_CONTROL,
    DEFAULT_MODEL,
    DEFAULT_NATURAL_LANGUAGE_CONTROL,
    DEVICE_CONFIGURATION_URL,
    DEVICE_MODEL,
    DOMAIN,
    MANUFACTURER,
)

_MAX_CONTROL_LENGTH = 8000


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
    """Set up editable MiMo TTS text entities."""
    sw_version = await hass.async_add_executor_job(_integration_sw_version)
    async_add_entities(
        [
            MimoControlTextEntity(
                hass,
                config_entry,
                sw_version,
                key=CONF_NATURAL_LANGUAGE_CONTROL,
                translation_key="natural_language_control",
            ),
            MimoControlTextEntity(
                hass,
                config_entry,
                sw_version,
                key=CONF_AUDIO_TAG_CONTROL,
                translation_key="audio_tag_control",
            ),
        ]
    )


class MimoControlTextEntity(TextEntity):
    """Editable MiMo v2.5 control text."""

    _attr_has_entity_name = True
    _attr_mode = TextMode.TEXT
    _attr_native_max = _MAX_CONTROL_LENGTH
    _attr_should_poll = False

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        sw_version: str,
        *,
        key: str,
        translation_key: str,
    ) -> None:
        self.hass = hass
        self._entry = config_entry
        self._key = key
        self._attr_translation_key = translation_key
        unique_base = config_entry.unique_id or config_entry.entry_id
        self._attr_unique_id = f"{unique_base}_{key}"
        default = (
            DEFAULT_NATURAL_LANGUAGE_CONTROL
            if key == CONF_NATURAL_LANGUAGE_CONTROL
            else DEFAULT_AUDIO_TAG_CONTROL
        )
        self._attr_native_value = (
            config_entry.data.get(key) or default
        ).strip()
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": DEFAULT_MODEL,
            "manufacturer": MANUFACTURER,
            "model": DEVICE_MODEL,
            "configuration_url": DEVICE_CONFIGURATION_URL,
            "sw_version": sw_version,
        }

    async def async_set_value(self, value: str) -> None:
        """Update the control text stored in the config entry."""
        control_text = value.strip()
        data: dict[str, Any] = {
            **self._entry.data,
            self._key: control_text,
        }
        self.hass.config_entries.async_update_entry(self._entry, data=data)
        self._attr_native_value = control_text
        self.async_write_ha_state()
