#!/usr/bin/env python3
"""配速校验：把解说文案段与视频场景窗口对齐，检查每段台词估算时长是否放得进对应窗口。

用法:
    python timing_planner.py --segments plan.json --speed 5.5 --video-duration 65 --output report.md

段 JSON 格式:
    {"segments": [
        {"id": 1, "text": "台词……", "start": 0.0, "end": 8.0, "type": "钩子", "scene": "残血反杀预兆"}
    ]}

判定规则:
    - 估算时长 > 窗口 + 0.5s      -> 超长（配音会溢出窗口，必须删减）
    - 估算时长 < 窗口 × 0.5       -> 过短（画面留白过多，建议扩充细节）
    - 其余                        -> ok
"""
import argparse
import json
import sys


def fmt_clock(t):
    """秒 -> mm:ss 或 hh:mm:ss。"""
    t = max(0.0, t)
    total_s = int(round(t))
    hh, rem = divmod(total_s, 3600)
    mm, ss = divmod(rem, 60)
    return f"{hh:02d}:{mm:02d}:{ss:02d}" if hh else f"{mm:02d}:{ss:02d}"


def main():
    ap = argparse.ArgumentParser(description="校验解说文案每段估算时长是否适配对应视频场景窗口")
    ap.add_argument("--segments", required=True, help="段 JSON 文件路径")
    ap.add_argument("--speed", type=float, default=5.0,
                    help="语速(字/秒)：解说 5.0-6.0，旁白 3.5-4.5，默认 5.0")
    ap.add_argument("--video-duration", type=float, default=None, help="视频总时长(秒)，用于校验越界")
    ap.add_argument("--output", default=None, help="报告 md 输出路径；不传则只打印")
    args = ap.parse_args()

    with open(args.segments, "r", encoding="utf-8") as f:
        data = json.load(f)
    segs = data["segments"]
    if not segs:
        print("错误: segments 为空", file=sys.stderr)
        sys.exit(1)

    for s in segs:
        if not str(s.get("text", "")).strip():
            print(f"⚠️ 段 {s.get('id')} 台词为空", file=sys.stderr)
        if float(s["start"]) >= float(s["end"]):
            print(f"⚠️ 段 {s.get('id')} 窗口 start>=end", file=sys.stderr)

    rows = []
    total_est = 0.0
    for s in segs:
        sid = s.get("id")
        text = str(s.get("text", ""))
        start, end = float(s["start"]), float(s["end"])
        window = end - start
        n = len(text)
        est = n / args.speed
        total_est += est
        if est > window + 0.5:
            status = "超长"
            suggest = f"删到≤{max(0, int((window - 0.3) * args.speed))}字"
        elif est < window * 0.5:
            status = "过短"
            suggest = f"扩到≈{int(window * 0.85 * args.speed)}字(画面细节)"
        else:
            status = "ok"
            suggest = "-"
        rows.append((sid, fmt_clock(start), fmt_clock(end), window, n, est, status, suggest))

    lines = [f"# 配速校验报告（语速 {args.speed} 字/秒）", "",
             "| 段 | 窗口 | 时长s | 字数 | 估算s | 状态 | 建议 |",
             "|---|---|---|---|---|---|---|"]
    for sid, cs, ce, window, n, est, status, suggest in rows:
        lines.append(f"| {sid} | {cs}–{ce} | {window:.1f} | {n} | {est:.1f} | {status} | {suggest} |")

    total_window = sum(float(s["end"]) - float(s["start"]) for s in segs)
    lines += ["", f"- 旁白估算总时长：{total_est:.1f}s；场景窗口总时长：{total_window:.1f}s"]
    if args.video_duration is not None:
        lines.append(f"- 视频总时长：{args.video_duration:.1f}s；旁白占比 {total_est / args.video_duration * 100:.0f}%")
        bad = [s.get("id") for s in segs if float(s["start"]) < 0 or float(s["end"]) > args.video_duration]
        if bad:
            lines.append(f"- ⚠️ 越界段：{bad}")

    n_ok = sum(1 for r in rows if r[6] == "ok")
    lines.append(f"- 达标 {n_ok}/{len(rows)} 段" + ("，全部通过 ✅" if n_ok == len(rows) else "，需修正 ⚠️"))
    report = "\n".join(lines)

    print(report)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report + "\n")
        print(f"\n报告已写入: {args.output}")


if __name__ == "__main__":
    main()
