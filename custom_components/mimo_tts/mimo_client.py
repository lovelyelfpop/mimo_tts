"""MiMo TTS: chat.completions + audio (WAV), official API."""

from __future__ import annotations

import base64
import binascii
import json
import logging
from typing import Any

import aiohttp

from .const import DEFAULT_MODEL
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

_LOGGER = logging.getLogger(__name__)

# Fixed output format per product requirements.
_AUDIO_FORMAT = "wav"

# MiMo TTS requires both user and assistant roles; speech is synthesized for the assistant turn.
_USER_PROMPT_READ_ALOUD = "Read the following text aloud."


def _extract_base64_audio(payload: dict[str, Any]) -> str:
    """Parse chat.completions response; audio is base64 in message.audio.data."""
    try:
        choice0 = payload["choices"][0]
        msg = choice0.get("message") or choice0.get("delta")
        if not isinstance(msg, dict):
            raise KeyError("message")
        audio = msg.get("audio")
        if isinstance(audio, dict) and audio.get("data"):
            return str(audio["data"])
        if isinstance(audio, str) and audio:
            return audio
    except (KeyError, IndexError, TypeError) as err:
        _LOGGER.debug("Primary audio parse failed: %s", err)

    try:
        data = payload.get("data")
        if isinstance(data, str) and data:
            return data
    except (TypeError, AttributeError):
        pass

    raise MimoAPIError(
        f"Response has no base64 audio in choices[0].message.audio.data: {str(payload)[:400]}"
    )


class MimoTTSClient:
    """POST chat/completions with audio block; response is JSON with base64 WAV."""

    def __init__(
        self,
        api_key: str,
        url: str,
    ) -> None:
        self._api_key = api_key
        self._url = url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "User-Agent": "HomeAssistant-MiMo-TTS",
            "Authorization": f"Bearer {self._api_key}",
        }

    def _build_chat_payload(self, text: str, *, voice: str) -> dict[str, Any]:
        messages: list[dict[str, str]] = [
            {"role": "user", "content": _USER_PROMPT_READ_ALOUD},
            {"role": "assistant", "content": text},
        ]

        return {
            "model": DEFAULT_MODEL,
            "messages": messages,
            "audio": {
                "format": _AUDIO_FORMAT,
                "voice": voice,
            },
        }

    _STATUS_MAP: dict[int, tuple[type[MimoAPIError], str]] = {
        400: (
            MimoBadRequestError,
            "Bad request — check JSON format, required params, and model name",
        ),
        401: (
            MimoAuthError,
            "Authentication failed — check API key and Authorization header",
        ),
        403: (
            MimoForbiddenError,
            "Access denied — region not supported or API key blocked",
        ),
        421: (
            MimoContentFilterError,
            "Content blocked by moderation — avoid unsafe or sensitive input",
        ),
        429: (
            MimoRateLimitError,
            "Rate limit exceeded — reduce request frequency or add backoff",
        ),
        500: (
            MimoServerError,
            "Server internal error — retry later",
        ),
        503: (
            MimoServiceUnavailableError,
            "Service unavailable — server overloaded, retry later",
        ),
    }

    def _raise_for_status(self, status: int, body: str) -> None:
        """Raise a specific exception based on the HTTP status code."""
        exc_cls, reason = self._STATUS_MAP.get(
            status, (MimoAPIError, "API request failed")
        )
        _LOGGER.error(
            "MiMo TTS HTTP %s from %s — %s. Body (truncated): %s",
            status,
            self._url,
            reason,
            body[:1200],
        )
        raise exc_cls(f"HTTP {status}: {reason} — {body[:500]}")

    async def async_synthesize(
        self,
        session: aiohttp.ClientSession,
        text: str,
        *,
        voice: str,
    ) -> tuple[bytes, str]:
        """Return raw WAV bytes and file extension for Home Assistant TTS cache."""
        payload = self._build_chat_payload(text, voice=voice)

        _LOGGER.debug(
            "MiMo TTS POST %s model=%s voice=%s msg_len=%s",
            self._url,
            payload.get("model"),
            (payload.get("audio") or {}).get("voice"),
            len(text),
        )

        try:
            async with session.post(
                self._url,
                json=payload,
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=120),
            ) as response:
                body_text = await response.text()
                if response.status >= 400:
                    self._raise_for_status(response.status, body_text)

                try:
                    body_json = json.loads(body_text)
                except json.JSONDecodeError as err:
                    _LOGGER.error(
                        "MiMo TTS JSON parse failed: %s. Raw (truncated): %s",
                        err,
                        body_text[:800],
                    )
                    raise MimoAPIError(f"Invalid JSON response: {err}") from err

                try:
                    b64 = _extract_base64_audio(body_json)
                except MimoAPIError:
                    _LOGGER.error(
                        "MiMo TTS could not find audio in JSON (truncated): %s",
                        str(body_json)[:800],
                    )
                    raise

                try:
                    raw = base64.b64decode(b64, validate=False)
                except binascii.Error as err:
                    _LOGGER.error("MiMo TTS base64 decode failed: %s", err)
                    raise MimoAPIError("Invalid base64 in audio.data") from err

                if not raw:
                    raise MimoAPIError("Decoded audio is empty")

                _LOGGER.debug("MiMo TTS success: %s bytes WAV", len(raw))
                return raw, _AUDIO_FORMAT

        except aiohttp.ClientError as err:
            _LOGGER.error(
                "MiMo TTS network error to %s: %s (%r)",
                self._url,
                err,
                type(err).__name__,
                exc_info=True,
            )
            raise MimoAPIError(f"Network error: {err}") from err
