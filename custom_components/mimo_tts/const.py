"""Constants for Xiaomi MiMo TTS."""

DOMAIN = "mimo_tts"

CONF_API_KEY = "api_key"
CONF_URL = "url"
CONF_STYLE = "style"

# Fixed model (no UI); see MiMo speech synthesis docs.
DEFAULT_MODEL = "mimo-v2-tts"
# Official chat.completions + audio; WAV only.
DEFAULT_CHAT_COMPLETIONS_URL = "https://api.xiaomimimo.com/v1/chat/completions"

# MiMo voice ids — chosen from HA `language` (zh → Chinese, else English).
VOICE_ZH = "mimo_default"
VOICE_EN = "default_en"


def voice_for_language(language: str | None) -> str:
    """Map HA TTS language to MiMo voice (only zh and en are supported)."""
    if not language:
        return VOICE_EN
    primary = language.lower().replace("_", "-").split("-")[0]
    if primary == "zh":
        return VOICE_ZH
    return VOICE_EN


# Device registry / device page (HA may show brand logo when manufacturer matches its asset set).
MANUFACTURER = "Xiaomi"
DEVICE_MODEL = "MiMo-V2-TTS"
DEVICE_CONFIGURATION_URL = "https://platform.xiaomimimo.com/"
