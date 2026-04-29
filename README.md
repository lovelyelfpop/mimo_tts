# Xiaomi MiMo TTS for Home Assistant

[English README](README_en.md)

在 Home Assistant 中使用 **MiMo-V2.5-TTS** 内置音色语音合成。  
小米官方文档：[MiMo-V2.5-TTS 语音合成](https://platform.xiaomimimo.com/docs/zh-CN/usage-guide/speech-synthesis-v2.5)。

## 安装
### 手动安装
下载[Release](https://github.com/manymuch/mimo_tts/releases)中最新的压缩包，解压后的`mimo_tts`文件夹复制到 HA 的 `custom_components/`内），重启HA，再在界面中搜索`mimo_tts`添加集成。  
### HACS安装
1. 安装 [HACS](https://hacs.xyz/)（如果尚未安装）
2. 在 HACS 选项卡中，点击右上角三个点，选择 `Custom repositories`
3. 将 `https://github.com/manymuch/mimo_tts` 粘贴到仓库地址，类型选择 `Integration`，点击 `添加`
4. 在搜索栏中搜索并选择 `Xiaomi MiMo TTS`
5. 点击 `下载`，然后重启 Home Assistant



## 添加集成配置

| 字段 | 说明 |
|------|------|
| **API key** | [Xiaomi API平台](https://platform.xiaomimimo.com/#/console/api-keys) 中获得的token |
| **URL** | 默认不用改：`https://api.xiaomimimo.com/v1/chat/completions` |
| **控制项** | 添加集成后，在集成设备中通过 `自然语言控制` 和 `音频标签控制` 两个文本实体查看和修改。`自然语言控制` 默认值为 `用轻快上扬的语调向领导报喜，语速稍快，带着查到成绩后压抑不住的激动与小骄傲，声音明亮有活力。`；`音频标签控制` 默认值为 `台湾腔`。 |


## 风格控制

### 自然语言控制

`自然语言控制` 会作为 MiMo v2.5 的 `user` 消息发送，用自然语言描述整体播报方式，例如语气、语速、情绪和角色状态。默认值为：

```
用轻快上扬的语调向领导报喜，语速稍快，带着查到成绩后压抑不住的激动与小骄傲，声音明亮有活力。
```

可以在集成设备的 `自然语言控制` 文本实体中修改。详见[小米官方说明](https://platform.xiaomimimo.com/docs/zh-CN/usage-guide/speech-synthesis-v2.5)。

### 音频标签控制

`音频标签控制` 会作为 MiMo v2.5 的音频标签加到 `assistant` 文本开头，默认值为 `台湾腔`。例如发送 `明天天气不错` 时，实际 `assistant` 文本为 `(台湾腔)明天天气不错`。

如果 `tts.say` 文本已经以音频标签开头，例如 `(开心)`、`（粤语）` 或 `[悄悄话]`，则使用文本中的标签，不再添加默认 `音频标签控制`。

| 通过 `tts.say` 发送的消息 | `assistant` 文本 |
|----|-----|
| `明天天气不错` | `(台湾腔)明天天气不错` |
| `(开心)明天就是周五了` | `(开心)明天就是周五了` |
| `(东北话 变快)哎呀妈呀，这天儿也忒冷了吧！` | `(东北话 变快)哎呀妈呀，这天儿也忒冷了吧！` |

## 音色
### 预置音色

集成会根据 Home Assistant 的语言选择 v2.5 预置音色。可在语言选择中使用以下值：

| 音色语言 | 音色 |
|---|---|
| 中文 | `冰糖` |
| 中文 | `茉莉` |
| 中文 | `苏打` |
| 中文 | `白桦` |
| 英文 | `Mia` |
| 英文 | `Chloe` |
| 英文 | `Milo` |
| 英文 | `Dean` |


### 定制音色

TODO：暂未实现。后续计划使用 `mimo-v2.5-tts-voicedesign` 支持定制音色；当前版本仅支持上方列出的 v2.5 预置音色。