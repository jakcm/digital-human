# 🤖 搞怪数字人 - AI 3D Talking Avatar

基于 **TalkingHead**（Three.js）的浏览器端 3D 互动数字人。

## 功能

- 🗣️ **说话** — 文本输入或语音输入，数字人开口说话（唇同步）
- 🎭 **表情** — 8 种情绪切换（开心/难过/生气/可爱/害怕/嫌弃/犯困/中性）
- 💃 **跳舞** — 可播放 3D 动画
- 🧠 **AI 对话** — 接入 LLM API（DeepSeek / OpenAI），人格：搞笑幽默豪爽带梗
- 🎤 **语音输入** — 浏览器麦克风语音识别（Chrome）

## 快速开始

### 在线访问

👉 [https://jakcm.github.io/digital-human/](https://jakcm.github.io/digital-human/)

### 配置

1. **LLM API Key** — 开启智能对话（支持 DeepSeek / OpenAI 兼容 API）
   - 推荐 DeepSeek：`https://api.deepseek.com/v1/chat/completions`
   - 模型：`deepseek-chat`
2. **Google TTS API Key** — 开启唇同步说话
   - 免费额度：100 万字符/月
   - 不填则使用浏览器 SpeechSynthesis（无唇同步）
3. **性格 Prompt** — 可以自定义数字人性格

### 本地运行

```bash
# 任意 HTTP 服务器即可
cd digital-human
python3 -m http.server 8000
# 浏览器打开 http://localhost:8000
```

## 技术栈

| 组件 | 技术 | 说明 |
|:----:|:----:|------|
| 3D 渲染 | Three.js | WebGL 浏览器 3D |
| 数字人引擎 | TalkingHead | 唇同步 + 表情 + 动画 |
| 3D 模型 | Ready Player Me | 免费，含 ARKit+Oculus Visemes |
| 语音合成 | Google TTS / Web Speech API | 可配置 |
| 语音识别 | Web Speech API | Chrome 内建 |
| AI 对话 | OpenAI 兼容 API | DeepSeek / 任何 LLM |
| 部署 | GitHub Pages | 免费静态托管 |

## 素材来源

- **3D 模型**: Ready Player Me（免费）
- **数字人引擎**: [TalkingHead](https://github.com/met4citizen/TalkingHead)（MIT）
- **Three.js**: MIT License

## 自定义

- 换模型：在设置中填入任意 GLB 模型 URL
- 换性格：修改 Prompt 即可
- 换声音：配置不同的 TTS API
