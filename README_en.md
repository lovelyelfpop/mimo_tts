# Xiaomi MiMo TTS for Home Assistant

[Chinese README](README.md)

Home Assistant integration for **MiMo-V2.5-TTS** built-in voice text-to-speech.  
Official docs: [MiMo-V2.5-TTS speech synthesis](https://platform.xiaomimimo.com/docs/zh-CN/usage-guide/speech-synthesis-v2.5).

## Installation
### Manual install
Copy the `mimo_tts` folder from the release archive into HA's `custom_components/` directory, restart HA, then search for `mimo_tts` in the UI to add the integration.
### Install with HACS
1. Install [HACS](https://hacs.xyz/) if you do not have that already
2. In the HACS Tab, click on the three dots at the top right and choose `Custom repositories`
3. Paste `https://github.com/manymuch/mimo_tts` to the repository field, choose the `Integration` category and click `ADD`
4. Search bar and select `Xiaomi MiMo TTS`
5. Click `DOWNLOAD` and restart Home Assistant



## Configuration

| Field | Description |
|--------|-------------|
| **API key** | Token from the [Xiaomi API platform](https://platform.xiaomimimo.com/#/console/api-keys) (required). |
| **URL** | Default (no change needed): `https://api.xiaomimimo.com/v1/chat/completions` |
| **Controls** | After setup, edit the Natural Language Control and Audio Tag Control text entities on the integration device. Natural Language Control defaults to a bright, bouncy good-news delivery; Audio Tag Control defaults to Taiwanese accent. |


## Speech Control

### Natural Language Control

Natural Language Control is sent as the MiMo v2.5 `user` message. Use it to describe the overall speaking style in natural language, such as tone, speed, emotion, and role state. The default value means:

```
Bright, bouncy, slightly sing-song tone — like you are bursting with good news you can barely hold in. Fast pace, rising pitch at the end.
```

You can edit it from the Natural Language Control text entity on the integration device. See the [official Xiaomi docs](https://platform.xiaomimimo.com/docs/zh-CN/usage-guide/speech-synthesis-v2.5).

### Audio Tag Control

Audio Tag Control is prepended to the MiMo v2.5 `assistant` text as an audio tag. The default value is Taiwanese accent. For example, when sending `The weather looks good tomorrow`, the actual `assistant` text is `(Taiwanese accent)The weather looks good tomorrow`.

If the `tts.say` text already starts with an audio tag, such as `(happy)`, `(Cantonese)`, or `[whisper]`, the inline tag is used and the default Audio Tag Control is not added.

| Message sent via `tts.say` | `assistant` text |
|----|-----|
| `The weather looks good tomorrow` | `(Taiwanese accent)The weather looks good tomorrow` |
| `(happy)Tomorrow is Friday. I'm so happy!` | `(happy)Tomorrow is Friday. I'm so happy!` |
| `(Northeastern accent, faster)Whoa, it is freezing out here!` | `(Northeastern accent, faster)Whoa, it is freezing out here!` |

## Voices
### Preset Voices

The integration selects v2.5 preset voices from the Home Assistant TTS language. Use these language values:

| Voice language | Voice |
|---|---|
| Chinese | `冰糖` |
| Chinese | `茉莉` |
| Chinese | `苏打` |
| Chinese | `白桦` |
| English | `Mia` |
| English | `Chloe` |
| English | `Milo` |
| English | `Dean` |


### Custom Voices

TODO: Not implemented yet. Future support for custom voices is planned with `mimo-v2.5-tts-voicedesign`; the current version only supports the v2.5 preset voices listed above.
