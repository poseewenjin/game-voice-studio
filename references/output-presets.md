# 成片预设（output-presets.md）

成片参数以「预设」为单位，用户一句话切换；未指定时用「默认·横屏解说」。

## 预设参数 Schema

| 参数 | 取值 | 说明 |
| --- | --- | --- |
| name | 预设名 | 用户点名用 |
| orientation | original / 9:16 | 保持原比例 / 竖屏中心裁切（会损失左右画面，交付时提示） |
| subtitle_style | 样式描述 | 传给 add-subtitle-to-video 的字幕样式（位置/字号/描边/颜色） |
| bgm | off / user | 关闭 / 用户提供 BGM 文件（只支持用户提供的文件，不自动生成） |
| original_audio | replace / keep_low | 替换原声 / 原声保留并压低 |
| fade | off / {in,out} | 片头片尾淡入淡出秒数 |

## 内置预设

### 默认·横屏解说（default）
- orientation: original；subtitle: 底部居中、白字黑边、中号；bgm: off；original_audio: replace；fade: off
- 适用：头条/快手/B站 常规解说

### 竖屏·快抖风
- orientation: 9:16（中心裁切，提示损失边缘画面）；subtitle: 底部居中大字、粗描边；bgm: 用户可选；original_audio: keep_low（压到 20%）；fade: in 0.3
- 适用：抖音/视频号/小红书 竖版

### 沉浸·剧情旁白
- orientation: original；subtitle: 居中偏下、细描边；bgm: user（旁白 80% / BGM 30%）；original_audio: replace；fade: in 1.0 / out 1.0
- 适用：剧情向、氛围向

### 直播切片·原声保留
- orientation: original；subtitle: 顶部小字（或按用户要求关闭）；bgm: off；original_audio: keep_low（压到 30%）；fade: off
- 适用：直播切片、多人口播，需保留现场声

## 自定义预设

用户一句话描述即生成：如「竖屏 + BGM 用这个文件 + 原声保留 + 片头 0.3 秒」→ 逐项映射；未提及项用默认值，并把最终参数写进交付说明。

## 执行要点

- **竖屏裁切**：对每个 scene 用 `crop-video` 中心裁成 9:16，再继续合流/字幕；提示会损失左右画面。
- **字幕样式**：把样式描述映射到 `add-subtitle-to-video` 的样式参数（先读该工具 reference 的可用字段）；工具不支持的样式降级为最接近的并说明。
- **原声保留压低**：scene 先 `extract-audio` 抽原音轨，与旁白按预设比例 `mix-audio` 混音，再 mux 回 scene；音量比例按 mix-audio reference 支持的参数设置，不支持时明确告知用户并采用可用方案。
- **BGM**：与旁白 `mix-audio` 混音，避免盖过人声（旁白 ≥ 70%）。
- **淡入淡出**：全部 scene 拼接后用 `fade-video-audio` 处理成片。
