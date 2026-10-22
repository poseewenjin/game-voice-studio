---
name: game-voice-studio
description: 游戏解说配音工坊。用户上传游戏视频（游戏实况/录屏/电竞切片），可附参考人声音频并设定人设，自动完成「画面分析→人设化解说/旁白文案→口播配音→按画面时间轴合成成片」全流水线，交付成片+文案稿+配音音频+画面分析摘要。触发场景：给游戏视频配解说或旁白、把游戏录屏做成解说视频、上传游戏视频+人声生成口播、游戏内容二创解说、按人设配音游戏画面等。也用于只为游戏视频写解说文案、只生成配音、或只做画面高光分析的单环节需求。
---

# 游戏解说配音工坊（game-voice-studio）

四角色专家团流水线：**画面分析师 → 文案师 → 配音导演 → 剪辑师**。把用户上传的游戏视频，变成「人设化解说/旁白文案 + 对应画面时间轴的配音 + 压制字幕的成片 + 全部中间素材」。

## 输入与默认

- **必填**：游戏视频（本地路径或 URL；mediakit 的 Cloud 输入适配器可直接处理本地路径）
- **选填**：参考人声音频（用于音色克隆；未提供时用预设音色）
- **选填**：人设描述（未提供时用默认人设「激情解说·老司机」并在交付中说明）
- **默认交付**：成片 + 解说文案稿 + 每段配音 + 旁白全轨 + 画面分析摘要（用户只要单环节时按需裁剪）

## 输出目录

在视频所在目录下建 `game_voice_<yyyyMMdd_HHmm>/`：

```
01_analysis/  画面分析摘要.md          （场景时间轴：窗口起止+画面内容+高光类型）
02_script/    解说文案稿.md、字幕.srt、字幕.json
03_voice/     段_<n>.wav …、旁白全轨.wav
04_final/     成片.mp4
```

## 专家团流水线

### 角色0 · 前置检查

1. 先读 `byted-mediakit-shared/SKILL.md`，执行可用性检查（`mediakit-cli --version`、`mediakit-cli --domains`）；再按需读 `byted-mediakit-video`、`byted-mediakit-editing`、`byted-mediakit-audio` 的 SKILL.md 及目标工具的 reference 与 `--schema`。
2. 配音用平台工具 `audio_to_audio_plus`（有参考人声）/ `text_to_audio_plus`（无参考人声），prompt 构造遵守 `seed-audio` skill 的规则。
3. Windows PowerShell 给 mediakit-cli 传 JSON 参数必须用 `--%`（整段 JSON 双引号包裹、内部引号转义），禁止单引号 JSON；详见 byted-mediakit-shared。
4. 探测视频元信息：`mediakit-cli video probe-video-metadata --video-url <video>`，记录总时长、分辨率。

### 角色1 · 画面分析师（产出场景时间轴）

目标：得到**场景时间轴**——每个场景窗口的起止时间 + 画面内容摘要 + 可讲点。

1. `mediakit-cli video analyze-video-highlights`（游戏/Game 模型）：得到带时间戳的高光事件、OCR、画面描述——这是「旁白对应画面」的主锚点。
2. 按视频类型补充：
   - 剧情向游戏：`analyze-video-storyline` 补充剧情分段；
   - UI/字幕/数值密集：`video-ocr`、`asr-subtitles`；
   - 关键画面核实（角色、操作、胜负、名场面）：`extract-frames` 抽帧后用 Read 逐帧查看，宁可核实不臆测。
3. 汇总成场景时间轴，每行：`窗口起止 | 画面内容 | 高光类型（开局/操作/团战/翻盘/名场面/彩蛋/失误）`，写入 `01_analysis/画面分析摘要.md`。

规则：分析结果必须能回答——画面里发生了什么、每个关键时刻在哪个时间窗、有哪些可讲的点（操作/胜负/槽点/名场面/数值变化）。

### 角色2 · 文案师（产出人设化文案并绑定画面时间轴）

1. 读 `references/personas.md`，确定人设（用户描述 > 模板 > 默认）。
2. 读 `references/script-patterns.md`，按结构模板写文案。
3. **每段文案必须绑定一个场景窗口** `[start, end]`；段内只讲当前画面内容，转场留白。
4. 字数约束：`段字数 ≈ 语速(字/秒) × 窗口时长(秒) × 0.85`（留呼吸与停顿）。
5. 运行 `scripts/timing_planner.py` 校验配速，按输出修正超长/过短段落（迭代直到全段 ok）。
6. 输出 `02_script/解说文案稿.md`，每段格式：

   ```
   [段号] 窗口 00:12–00:35 | 类型: 操作解说 | 画面: 团战爆发
   台词……
   ```

7. 运行 `scripts/build_srt.py` 生成字幕 `.srt` 与 mediakit 用 `.json`。

### 角色3 · 配音导演（人设音色朗读文案）

1. **有参考人声** → `audio_to_audio_plus`：`audio_reference_url_list` 传参考人声 URL（本地文件先上传取 URL），prompt 按 A2A 规则构造，例如 `用@音频1的音色，{人设语气、口癖}，{台词}`。
2. **无参考人声** → `text_to_audio_plus`：prompt 直接描述人设音色与语气。
3. **逐段生成**（不要整篇一次生成）：每段一个 wav，命名 `段_<n>.wav`，便于按画面时间轴对齐。
4. 生成后用 `mediakit-cli audio probe-audio-metadata` 探测每段实际时长。
5. 时长超差处理：
   - 实际时长 > 窗口时长 + 0.5s → 删减台词重生成，或 `adjust-audio-speed` 微调（±5% 内）；
   - 实际时长 < 窗口时长 × 0.5 → 检查是否吞字/漏句，必要时重生成。
6. 全部段落按序 `concat-audio` 拼接为 `旁白全轨.wav`（素材，供用户单独取用；与画面的严格对齐在第4步按场景完成）。

### 角色4 · 剪辑师（按画面时间轴合成成片）

按场景窗口逐段处理，保证「说到哪、画面是哪」：

1. 对每个场景窗口 i：`mediakit-cli editing trim-video` 从原视频截 `[start, end]` → `scene_<i>.mp4`。
2. `mediakit-cli editing mux-audio-video`：scene + 段_i.wav，替换音轨（时长不一致时按需对齐）。
3. `mediakit-cli editing add-subtitle-to-video`：用该段字幕 JSON 压制 → `scene_<i>_done.mp4`。
4. 全部 `scene_<i>_done.mp4` 按序 `concat-video`（可加转场）→ `04_final/成片.mp4`。
5. 可选（用户要求保留原声时）：`extract-audio` 抽原音轨 → 调低音量 → `mix-audio` 混入旁白 → 再 mux；可选 `fade-video-audio` 做片头片尾淡入淡出。

## 交付清单（全部交付）

- `04_final/成片.mp4`
- `02_script/解说文案稿.md`（含时间轴对应）+ 字幕 `.srt`/`.json`
- `03_voice/段_<n>.wav` 与 `旁白全轨.wav`
- `01_analysis/画面分析摘要.md`

## 验证

- **成片回读**：抽取 2–3 个时间点核对，旁白内容与画面吻合、字幕同步不提前不滞后。
- **时长**：成片时长 ≈ 原视频时长（或用户指定时长）；旁白总时长 ≤ 原视频时长。
- **字幕**：.srt/.json 与文案稿逐段一致，无错字漏句。
- **人设**：抽查 3 处台词符合人设语气、口癖、称谓。

## 质量红线

- 不捏造画面里没有的内容；证据不足就抽帧核实，分析摘要中标注「已核实/推测」。
- 游戏名、角色名、版本、赛事/主播名必须与画面一致，不写未经证实的信息。
- 不低俗、不引战、不剧透（解说视角不提前说结局）。
- 「首播/独家/全网首发」等表述须用户确认后才写。
- 涉及版权音乐/BGM 时提示用户替换为自有或授权素材。
