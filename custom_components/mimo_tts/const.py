"""Constants for Xiaomi MiMo TTS."""

DOMAIN = "mimo_tts"

CONF_API_KEY = "api_key"
CONF_URL = "url"
CONF_NATURAL_LANGUAGE_CONTROL = "natural_language_control"
CONF_AUDIO_TAG_CONTROL = "audio_tag_control"
DEFAULT_NATURAL_LANGUAGE_CONTROL = (
    "用轻快上扬的语调向领导报喜，语速稍快，带着查到成绩后压抑不住的激动与小骄傲，声音明亮有活力。"
)
DEFAULT_AUDIO_TAG_CONTROL = "台湾腔"
OPTION_NATURAL_LANGUAGE_CONTROL = "natural_language_control"
OPTION_AUDIO_TAG_CONTROL = "audio_tag_control"

# Fixed model (no UI); see MiMo speech synthesis v2.5 docs.
DEFAULT_MODEL = "mimo-v2.5-tts"
# Official chat.completions + audio; WAV only.
DEFAULT_CHAT_COMPLETIONS_URL = "https://api.xiaomimimo.com/v1/chat/completions"

# Real HA language codes this engine advertises (BCP-47 tags).
LANG_ZH_CN = "zh-CN"
LANG_EN_US = "en-US"

SUPPORTED_LANGUAGES = [LANG_ZH_CN, LANG_EN_US]

# MiMo v2.5 built-in voice ids.
VOICE_ZH_BINGTANG = "冰糖"
VOICE_ZH_MOLI = "茉莉"
VOICE_ZH_SUDA = "苏打"
VOICE_ZH_BAIHUA = "白桦"
VOICE_EN_MIA = "Mia"
VOICE_EN_CHLOE = "Chloe"
VOICE_EN_MILO = "Milo"
VOICE_EN_DEAN = "Dean"

VOICES_BY_LANGUAGE: dict[str, list[str]] = {
    LANG_ZH_CN: [
        VOICE_ZH_BINGTANG,
        VOICE_ZH_MOLI,
        VOICE_ZH_SUDA,
        VOICE_ZH_BAIHUA,
    ],
    LANG_EN_US: [
        VOICE_EN_MIA,
        VOICE_EN_CHLOE,
        VOICE_EN_MILO,
        VOICE_EN_DEAN,
    ],
}

DEFAULT_VOICE_BY_LANGUAGE: dict[str, str] = {
    LANG_ZH_CN: VOICE_ZH_BINGTANG,
    LANG_EN_US: VOICE_EN_MIA,
}


def _has_leading_audio_tag(text: str) -> bool:
    """Return whether text already starts with a MiMo audio tag."""
    stripped = text.lstrip()
    tag_pairs = (("(", ")"), ("（", "）"), ("[", "]"))
    return any(
        stripped.startswith(open_tag) and close_tag in stripped[1:]
        for open_tag, close_tag in tag_pairs
    )


def apply_audio_tag_control(text: str, audio_tag_control: str | None) -> str:
    """Apply MiMo v2.5 tag control to assistant text."""
    if _has_leading_audio_tag(text):
        return text

    style = (audio_tag_control or "").strip()
    if not style:
        return text

    if (
        (style.startswith("(") and style.endswith(")"))
        or (style.startswith("（") and style.endswith("）"))
        or (style.startswith("[") and style.endswith("]"))
    ):
        style = style[1:-1].strip()
    if not style:
        return text

    return f"({style}){text}"


def _normalize_language(language: str | None) -> str | None:
    """Return the canonical supported language tag for a HA language code."""
    if language is None:
        return None
    raw = language.strip().replace("_", "-")
    for key in VOICES_BY_LANGUAGE:
        if raw.casefold() == key.casefold():
            return key
    base = raw.split("-", 1)[0].casefold()
    for key in VOICES_BY_LANGUAGE:
        if key.split("-", 1)[0].casefold() == base:
            return key
    return None


def voices_for_language(language: str | None) -> list[str] | None:
    """Return MiMo built-in voice ids available for a language code."""
    lang = _normalize_language(language)
    if lang is None:
        return None
    return VOICES_BY_LANGUAGE[lang]


def voice_for_language(language: str | None) -> str:
    """Return the default MiMo voice id for a HA language code."""
    lang = _normalize_language(language)
    if lang is not None:
        return DEFAULT_VOICE_BY_LANGUAGE[lang]
    return DEFAULT_VOICE_BY_LANGUAGE[SUPPORTED_LANGUAGES[0]]


# Device registry / device page (HA may show brand logo when manufacturer matches its asset set).
MANUFACTURER = "Xiaomi"
DEVICE_MODEL = "MiMo-V2.5-TTS"
DEVICE_CONFIGURATION_URL = (
    "https://platform.xiaomimimo.com/docs/zh-CN/usage-guide/speech-synthesis-v2.5"
)
