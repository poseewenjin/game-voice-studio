#!/usr/bin/env python3
"""把解说文案段转成字幕文件：.srt（通用）与 .json（mediakit add-subtitle-to-video 用）。

用法:
    python build_srt.py --segments plan.json --outdir 02_script --speed 5.5

段 JSON 格式（同 timing_planner）:
    {"segments": [
        {"id": 1, "text": "台词……", "start": 0.0, "end": 8.0, "type": "钩子", "scene": "残血反杀预兆"}
    ]}

字幕时间规则: 起点=场景窗口起点；终点=min(窗口终点, 起点+估算朗读时长+0.3s)，
让字幕跟着说话走、不拖尾。估算朗读时长 = 字数 / 语速。
"""
import argparse
import json
import os


def fmt_srt(t):
    """秒 -> SRT 时间戳 hh:mm:ss,mmm。"""
    total_ms = int(round(max(0.0, t) * 1000))
    hh, rem = divmod(total_ms, 3600000)
    mm, rem = divmod(rem, 60000)
    ss, mmm = divmod(rem, 1000)
    return f"{hh:02d}:{mm:02d}:{ss:02d},{mmm:03d}"


def main():
    ap = argparse.ArgumentParser(description="生成字幕 .srt 与 .json")
    ap.add_argument("--segments", required=True, help="段 JSON 文件路径")
    ap.add_argument("--outdir", required=True, help="输出目录")
    ap.add_argument("--speed", type=float, default=5.0, help="语速(字/秒)，用于估算字幕终点，默认 5.0")
    args = ap.parse_args()

    with open(args.segments, "r", encoding="utf-8") as f:
        data = json.load(f)
    segs = data["segments"]
    if not segs:
        raise SystemExit("错误: segments 为空")

    os.makedirs(args.outdir, exist_ok=True)
    srt_lines = []
    sub_json = []
    for i, s in enumerate(segs, 1):
        start, end = float(s["start"]), float(s["end"])
        text = str(s.get("text", "")).strip()
        est = len(text) / args.speed
        sub_end = min(end, start + est + 0.3)
        srt_lines += [str(i), f"{fmt_srt(start)} --> {fmt_srt(sub_end)}", text, ""]
        sub_json.append({"start_time": start, "end_time": round(sub_end, 3), "subtitle_text": text})

    srt_path = os.path.join(args.outdir, "subtitles.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))
    json_path = os.path.join(args.outdir, "subtitles.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(sub_json, f, ensure_ascii=False, indent=2)

    print(f"已生成: {srt_path}（{len(segs)} 条）")
    print(f"已生成: {json_path}")
    print("提示: add-subtitle-to-video 使用 subtitles.json；Windows PowerShell 传 JSON 参数用 --% 双引号包裹。")


if __name__ == "__main__":
    main()
