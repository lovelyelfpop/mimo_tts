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

# MiMo v2.5 built-in voice ids — chosen from HA `language`.
LANG_ZH_BINGTANG = "冰糖"
LANG_ZH_MOLI = "茉莉"
LANG_ZH_SUDA = "苏打"
LANG_ZH_BAIHUA = "白桦"
LANG_EN_MIA = "Mia"
LANG_EN_CHLOE = "Chloe"
LANG_EN_MILO = "Milo"
LANG_EN_DEAN = "Dean"

SUPPORTED_LANGUAGES = [
    LANG_ZH_BINGTANG,
    LANG_ZH_MOLI,
    LANG_ZH_SUDA,
    LANG_ZH_BAIHUA,
    LANG_EN_MIA,
    LANG_EN_CHLOE,
    LANG_EN_MILO,
    LANG_EN_DEAN,
]

_VOICE_BY_LANGUAGE = {
    LANG_ZH_BINGTANG: "冰糖",
    LANG_ZH_MOLI: "茉莉",
    LANG_ZH_SUDA: "苏打",
    LANG_ZH_BAIHUA: "白桦",
    LANG_EN_MIA: "Mia",
    LANG_EN_CHLOE: "Chloe",
    LANG_EN_MILO: "Milo",
    LANG_EN_DEAN: "Dean",
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


def voice_for_language(language: str | None) -> str:
    """Map HA TTS language selection to a MiMo v2.5 built-in voice."""
    if language is None:
        language = SUPPORTED_LANGUAGES[0]
    normalized = language.strip().replace("_", "-")
    return _VOICE_BY_LANGUAGE[normalized]


# Device registry / device page (HA may show brand logo when manufacturer matches its asset set).
MANUFACTURER = "Xiaomi"
DEVICE_MODEL = "MiMo-V2.5-TTS"
DEVICE_CONFIGURATION_URL = (
    "https://platform.xiaomimimo.com/docs/zh-CN/usage-guide/speech-synthesis-v2.5"
)
