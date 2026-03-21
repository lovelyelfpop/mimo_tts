# Xiaomi MiMo TTS for Home Assistant

[中文说明](README.md)

Home Assistant integration for **MiMo-V2-TTS** text-to-speech.  
Official docs: [platform.xiaomimimo.com](https://platform.xiaomimimo.com/).

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
| **Default style** | Optional. A style string automatically prepended as `<style>…</style>` to every TTS request. If a message already contains its own `<style>` tag, the default is ignored and the inline style takes precedence. |


## Style control

### Overall style control

Use `<style>` in `tts.say` to set one or more styles. See the [official Xiaomi docs](https://platform.xiaomimimo.com/#/docs/news/v2-tts-release) for details.

* Single style: `<style>style1</style>Text to speak`
* Multiple styles: `<style>style1 style2</style>Text to speak`

For a full list of recommended styles (speed, emotion, role-play, dialect, etc.) and fine-grained audio tag examples, see the [Chinese README](README.md).

### Default style behaviour

When a **Default style** is configured, every `tts.say` call automatically prepends `<style>style</style>`.  
You can override the default by specifying a style directly in `tts.say`.  
For example, if the default style is set to `温柔女声`:

| Message sent via `tts.say` | Text actually synthesized |
|----|-----|
| `明天天气不错` | `<style>温柔女声</style>明天天气不错` |
| `<style>开心</style>明天就是周五了` | `<style>开心</style>明天就是周五了` (inline style wins) |

### Fine-grained control with audio tags

Use inline audio tags in your text for precise control over tone, emotion, and expression — whispers, laughter, sighs, coughs, breathing, pauses, and tempo changes. See the [Chinese README](README.md) for examples.
