# VOICEVOX OpenAPI 3.1.0 规格分析

**引擎版本**: 0.25.0
**文档日期**: 2025-12-13

---

## 1. 核心 TTS 工作流程

VOICEVOX 的音声合成分为两个步骤：

```
┌─────────────────────────────────────────────────────┐
│         步骤 1: 获取音声合成查询 (AudioQuery)         │
│                                                     │
│  POST /audio_query                                  │
│  参数: text (str), speaker (int)                    │
│  响应: AudioQuery 对象                              │
│  ↓                                                  │
│  (包含音高、语速、声调等参数的完整配置)              │
└─────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────┐
│           步骤 2: 进行音声合成 (合成)                │
│                                                     │
│  POST /synthesis                                    │
│  参数: speaker (int)                                │
│  请求体: AudioQuery (JSON)                          │
│  响应: 音频文件 (audio/wav - 二进制)                │
└─────────────────────────────────────────────────────┘
```

---

## 2. 核心 TTS 端点详解

### 2.1 `/audio_query` - 获取音声合成查询参数

**HTTP 方法**: POST
**功能**: 生成音声合成的初始化查询对象，可直接用于合成

**请求参数** (Query Parameters):

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `text` | string | ✓ | - | 要合成的文本 |
| `speaker` | integer | ✓ | - | 发言人ID (通过 `/speakers` 获取) |
| `enable_katakana_english` | boolean | ✗ | true | 是否启用片假名英文转换 |
| `core_version` | string | ✗ | - | 指定使用的核心版本 |

**响应格式** (HTTP 200):

```json
{
  "Content-Type": "application/json",
  "schema": "AudioQuery"
}
```

**错误响应**:
- HTTP 422: 验证错误 (HTTPValidationError)

**使用示例**:
```bash
curl -X POST "http://localhost:50021/audio_query?text=こんにちは&speaker=0"
```

---

### 2.2 `/synthesis` - 音声合成 (生成音频)

**HTTP 方法**: POST
**功能**: 基于 AudioQuery 对象生成 WAV 格式音频文件

**请求参数** (Query Parameters):

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `speaker` | integer | ✓ | - | 发言人ID |
| `enable_interrogative_upspeak` | boolean | ✗ | true | 疑问句是否自动调整语调 |
| `core_version` | string | ✗ | - | 指定使用的核心版本 |

**请求体** (RequestBody):

```json
{
  "Content-Type": "application/json",
  "schema": "AudioQuery"  // 从 /audio_query 获取的对象
}
```

**响应格式** (HTTP 200):

```
Content-Type: audio/wav
Body: 二进制音频数据 (WAV 格式)
```

**错误响应**:
- HTTP 422: 验证错误 (HTTPValidationError)

**使用示例**:
```bash
# 第一步：获取查询
curl -X POST "http://localhost:50021/audio_query?text=こんにちは&speaker=0" > query.json

# 第二步：合成音频
curl -X POST "http://localhost:50021/synthesis?speaker=0" \
  -H "Content-Type: application/json" \
  -d @query.json \
  --output output.wav
```

---

## 3. AudioQuery 对象详解

**说明**: 音声合成用的完整查询配置对象

### 3.1 结构

```json
{
  "accent_phrases": [
    {
      "moras": [
        {
          "text": "コ",
          "consonant": "k",
          "consonant_length": 0.05,
          "vowel": "o",
          "vowel_length": 0.1,
          "pitch": 5.5
        }
      ],
      "accent": 1,
      "pause_mora": null,
      "is_interrogative": false
    }
  ],
  "speedScale": 1.0,
  "pitchScale": 1.0,
  "intonationScale": 1.0,
  "volumeScale": 1.0,
  "prePhonemeLength": 0.1,
  "postPhonemeLength": 0.1,
  "pauseLength": null,
  "pauseLengthScale": 1.0,
  "outputSamplingRate": 44100,
  "outputStereo": false,
  "kana": "[読み取り専用] AquesTalk形式の読み"
}
```

### 3.2 核心字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `accent_phrases` | AccentPhrase[] | **必需**: 重音短语列表（由引擎自动生成） |
| `speedScale` | number | **必需**: 全体语速倍数 (0.5=慢, 2.0=快) |
| `pitchScale` | number | **必需**: 全体音高调整 (0.5=低, 2.0=高) |
| `intonationScale` | number | **必需**: 全体语调/抑扬程度 |
| `volumeScale` | number | **必需**: 全体音量倍数 |
| `prePhonemeLength` | number | **必需**: 音声开始前的静音时间 |
| `postPhonemeLength` | number | **必需**: 音声结束后的静音时间 |
| `pauseLength` | number\|null | 句读点等的静音时间 (null=忽略，默认值=null) |
| `pauseLengthScale` | number | 句读点等的静音时间倍数 (默认值=1) |
| `outputSamplingRate` | integer | **必需**: 输出音频采样率 (通常 44100 或 48000) |
| `outputStereo` | boolean | **必需**: 是否输出立体声 (false=单声道) |
| `kana` | string | 只读: AquesTalk 风格的读音标记 |

### 3.3 AccentPhrase 结构

```json
{
  "moras": [Mora],      // 音节列表
  "accent": 1,          // 重音位置 (从句首开始的索引)
  "pause_mora": Mora|null,  // 末尾无音节点 (null=不添加)
  "is_interrogative": false // 是否为疑问句 (默认=false)
}
```

### 3.4 Mora (音节) 结构

```json
{
  "text": "コ",
  "consonant": "k",
  "consonant_length": 0.05,
  "vowel": "o",
  "vowel_length": 0.1,
  "pitch": 5.5
}
```

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `text` | string | ✓ | 文字表示 |
| `consonant` | string | ✗ | 子音音素 (如 "k", "s") |
| `consonant_length` | number | ✗ | 子音长度 (秒) |
| `vowel` | string | ✓ | 母音音素 (如 "o", "a") |
| `vowel_length` | number | ✓ | 母音长度 (秒) |
| `pitch` | number | ✓ | 音高 (Hz) |

---

## 4. Speaker (发言人) 管理

### 4.1 `/speakers` - 获取可用发言人列表

**HTTP 方法**: GET
**功能**: 获取所有可用的发言人及其样式

**请求参数**:

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `core_version` | string | ✗ | 指定核心版本 |

**响应格式** (HTTP 200):

```json
{
  "Content-Type": "application/json",
  "schema": "Speaker[]"  // 发言人数组
}
```

**使用示例**:
```bash
curl "http://localhost:50021/speakers"
```

### 4.2 Speaker 对象结构

```json
{
  "name": "四国めたる",
  "speaker_uuid": "7ffcb7ce-00bd-45a8-a470-1cc1912d4186",
  "styles": [
    {
      "name": "ノーマル",
      "id": 0,
      "type": "talk"
    },
    {
      "name": "アンガー",
      "id": 1,
      "type": "talk"
    }
  ],
  "version": "0.0.1",
  "supported_features": {
    "permitted_synthesis_morphing": "ALL"
  }
}
```

**Speaker 对象字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 发言人名称 |
| `speaker_uuid` | string | 发言人唯一标识符 (UUID) |
| `styles` | SpeakerStyle[] | 样式列表 |
| `version` | string | 版本号 |
| `supported_features` | SpeakerSupportedFeatures | 支持的功能 |

**SpeakerStyle 对象**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 样式名称 (如 "标准", "愤怒") |
| `id` | integer | 样式ID (用于 `/audio_query` 的 `speaker` 参数) |
| `type` | string | 样式类型: `talk` (对话), `singing_teacher` (歌唱教师), `frame_decode`, `sing` (歌唱) |

**SpeakerSupportedFeatures**:

| 字段 | 类型 | 可选值 | 说明 |
|------|------|--------|------|
| `permitted_synthesis_morphing` | string | `ALL`, `SELF_ONLY`, `NOTHING` | 变形功能权限 (ALL=全许可, SELF_ONLY=同角色内许可, NOTHING=禁止) |

### 4.3 `/speaker_info` - 获取特定发言人的详细信息

**HTTP 方法**: GET
**功能**: 获取指定发言人的详细信息 (包括肖像、样式信息等)

**请求参数**:

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `speaker_uuid` | string | ✓ | - | 发言人UUID (来自 `/speakers`) |
| `resource_format` | string | ✗ | base64 | 资源格式: `base64` 或 `url` |

---

## 5. 版本和健康检查

### 5.1 `/version` - 获取引擎版本

**HTTP 方法**: GET
**响应**: 版本字符串 (如 "0.25.0")

```bash
curl "http://localhost:50021/version"
# 响应: "0.25.0"
```

### 5.2 `/core_versions` - 获取可用的核心版本列表

**HTTP 方法**: GET
**响应**: 版本字符串数组

```bash
curl "http://localhost:50021/core_versions"
# 响应: ["0.25.0", "0.24.0", ...]
```

**注**: VOICEVOX API 规格中没有明确的 `/health` 端点，但可以使用 `/version` 来验证服务器健康状态

---

## 6. 高级功能端点

### 6.1 `/accent_phrases` - 获取重音短语

**HTTP 方法**: POST
**功能**: 从文本生成重音短语列表 (不进行完整合成)

**请求参数**:

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `text` | string | ✓ | - | 输入文本 |
| `speaker` | integer | ✓ | - | 发言人ID |
| `is_kana` | boolean | ✗ | false | 文本是否为 AquesTalk 风格的假名 |
| `enable_katakana_english` | boolean | ✗ | true | 是否启用片假名英文转换 |
| `core_version` | string | ✗ | - | 核心版本 |

**响应**: AccentPhrase[] 数组

**AquesTalk 假名格式说明** (当 `is_kana=true`):
- 所有假名用片假名表示
- 重音短语用 `/` 或 `、` 分隔 (`、` 会插入停顿)
- 字符前加 `_` 可使其无声化
- 用 `'` 指定重音位置 (必须为每个短语指定)
- 短语末加 `？` (全角) 可标记为疑问句

**示例**:
```
こん'にちは / 世界
```

### 6.2 `/synthesis_morphing` - 音声合成变形

**功能**: 在多个发言人之间进行变形/插值合成

**说明**: 支持在不同发言人的声音之间进行平滑过渡

---

## 7. 错误处理和 HTTP 状态码

### 7.1 HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求格式错误 (如 KanaParser 失败) |
| 422 | 验证错误 (Validation Error) |
| 500+ | 服务器错误 |

### 7.2 验证错误响应 (HTTP 422)

**HTTPValidationError 结构**:

```json
{
  "detail": [
    {
      "loc": ["query", "speaker"],
      "msg": "value is not a valid integer",
      "type": "type_error.integer"
    }
  ]
}
```

### 7.3 Kana 解析错误响应 (HTTP 400)

**ParseKanaBadRequest 结构**:

```json
{
  "text": "エラーメッセージ",
  "error_name": "UNKNOWN_TEXT",
  "error_args": {
    "text": "判別できない読み仮名があります: ..."
  }
}
```

**可能的错误名称**:

| 错误名 | 说明 |
|--------|------|
| `UNKNOWN_TEXT` | 判别不了的假名: {text} |
| `ACCENT_TOP` | 句首不能放置重音: {text} |
| `ACCENT_TWICE` | 一个重音短语中不能有两个以上的重音: {text} |
| `ACCENT_NOTFOUND` | 存在没有指定重音的重音短语: {text} |
| `EMPTY_PHRASE` | 第 {position} 个重音短语为空白 |
| `INTERROGATION_MARK_NOT_AT_END` | "?" 只能放在短语末尾: {text} |
| `INFINITE_LOOP` | 处理时出现无限循环 (请报告 bug) |

---

## 8. 最小化 TTS 客户端实现

### 8.1 核心工作流程 (Python 示例)

```python
import requests
import json

API_URL = "http://localhost:50021"

def synthesize(text: str, speaker_id: int = 0) -> bytes:
    """
    最小化的 TTS 实现：获取查询 → 合成 → 返回音频
    """
    # 步骤 1: 获取 AudioQuery
    response = requests.post(
        f"{API_URL}/audio_query",
        params={"text": text, "speaker": speaker_id}
    )
    response.raise_for_status()
    audio_query = response.json()

    # 步骤 2: 进行合成
    response = requests.post(
        f"{API_URL}/synthesis",
        json=audio_query,
        params={"speaker": speaker_id}
    )
    response.raise_for_status()

    return response.content  # 返回 WAV 字节数据

# 使用示例
audio_data = synthesize("こんにちは世界")
with open("output.wav", "wb") as f:
    f.write(audio_data)
```

### 8.2 获取可用发言人列表

```python
def get_speakers() -> list:
    """获取可用的发言人列表"""
    response = requests.get(f"{API_URL}/speakers")
    response.raise_for_status()
    return response.json()

# 使用示例
speakers = get_speakers()
for speaker in speakers:
    print(f"{speaker['name']}: {speaker['speaker_uuid']}")
    for style in speaker['styles']:
        print(f"  - {style['name']} (ID: {style['id']})")
```

### 8.3 高级: 调整语音参数

```python
def synthesize_with_params(
    text: str,
    speaker_id: int = 0,
    speed: float = 1.0,
    pitch: float = 1.0,
    volume: float = 1.0
) -> bytes:
    """合成带有自定义参数的音频"""

    # 获取基础查询
    response = requests.post(
        f"{API_URL}/audio_query",
        params={"text": text, "speaker": speaker_id}
    )
    response.raise_for_status()
    audio_query = response.json()

    # 修改参数
    audio_query["speedScale"] = speed
    audio_query["pitchScale"] = pitch
    audio_query["volumeScale"] = volume

    # 合成
    response = requests.post(
        f"{API_URL}/synthesis",
        json=audio_query,
        params={"speaker": speaker_id}
    )
    response.raise_for_status()

    return response.content

# 使用示例：快速、高音、大音量
audio_data = synthesize_with_params(
    "こんにちは",
    speed=1.5,
    pitch=1.2,
    volume=1.1
)
```

---

## 9. 配置和部署

### 9.1 API 端点基本信息

| 项 | 值 |
|-----|-----|
| 默认主机 | http://localhost:50021 |
| 协议 | HTTP (部分部署支持 HTTPS) |
| 文档格式 | OpenAPI 3.1.0 |
| 自动文档 | 通常在 `/docs` (Swagger UI) 或 `/redoc` |

### 9.2 常见错误和解决方案

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| 连接拒绝 | VOICEVOX 未运行 | 启动 VOICEVOX 引擎 |
| 422 错误 | 参数类型错误 | 检查 `speaker` 是否为整数 |
| 400 错误 | Kana 解析失败 | 检查假名格式或禁用 `is_kana` |
| 服务器超时 | 引擎资源不足 | 减少并发请求或增加硬件资源 |

---

## 10. 功能对比表

### 最小集合 vs 完整集合

| 功能 | 端点 | 必需? | 难度 | 说明 |
|------|------|-------|------|------|
| 基础合成 | `/audio_query`, `/synthesis` | ✓ | 简单 | 核心功能，全部需要 |
| 获取发言人 | `/speakers` | ✓ | 简单 | 需要知道 speaker ID |
| 调整语速/音高 | 修改 AudioQuery | ✓ | 简单 | 直接编辑 JSON 字段 |
| 重音短语编辑 | `/accent_phrases`, 修改 AudioQuery | ✗ | 中等 | 高级功能，可选 |
| 变形合成 | `/synthesis_morphing` | ✗ | 困难 | 特殊功能，大多数应用不需要 |
| 版本检查 | `/version`, `/core_versions` | ✗ | 简单 | 可选，用于兼容性检查 |

---

## 总结

**最小化 TTS 实现** (3 个 API 调用):

1. `GET /speakers` - 获取可用发言人列表（初始化时）
2. `POST /audio_query` - 为输入文本生成合成参数
3. `POST /synthesis` - 基于参数生成音频

**核心参数调整** (修改 AudioQuery):

- `speedScale` - 语速 (0.5-2.0 范围通常安全)
- `pitchScale` - 音高 (0.5-2.0)
- `volumeScale` - 音量 (0.5-2.0)
- `intonationScale` - 语调表现力

**错误处理**:
- 422: 参数验证错误 → 检查参数类型
- 400: Kana 解析错误 → 检查文本格式或禁用 `is_kana`
- 其他: 服务器错误 → 检查 VOICEVOX 是否运行

---

## 文件位置

- **OpenAPI 规格文件**: `F:\repo\claude-voice-hooks\voicevox_api.json`
- **本分析文档**: `F:\repo\claude-voice-hooks\VOICEVOX_API_ANALYSIS.md`
