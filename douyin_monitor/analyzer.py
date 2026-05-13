#!/usr/bin/env python3
"""
抖音直播内容分析工具
====================
全自动流程：检测开播 → 录制音频 → Whisper 转文字 → Claude 生成摘要

用法
----
# 监控某用户，开播时自动分析（最常用）:
  python analyzer.py watch --user-id 123456 --cookies "ttwid=xxx; sid_tt=yyy"

# 直接分析正在直播的房间 (room_id 是数字):
  python analyzer.py fetch --room-id 7234567890123 --cookies "ttwid=xxx"

# 使用更小的 Whisper 模型加速（精度略低）:
  python analyzer.py watch --user-id 123456 --whisper-model small

# 每 10 分钟出一次阶段摘要，结果保存到文件:
  python analyzer.py watch --user-id 123456 --chunk-minutes 10 --output summary.md

环境变量
--------
  ANTHROPIC_API_KEY   Claude API 密钥（也可用 --api-key 传入）

依赖安装
--------
  pip install httpx faster-whisper anthropic

系统依赖
--------
  ffmpeg（sudo apt install ffmpeg 或 brew install ffmpeg）

Cookie 获取方法
--------------
  1. 浏览器打开 https://live.douyin.com 并登录
  2. F12 → Application → Cookies → 复制 ttwid 和 sid_tt 的值
  3. --cookies "ttwid=<值>; sid_tt=<值>"
"""
import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from checker import DouyinChecker, LiveInfo
from audio_capture import AudioCapture
from transcriber import Transcriber
from summarizer import Summarizer

# ── terminal colours ─────────────────────────────────────────────────────────
_R = "\033[0m"
_BOLD = "\033[1m"
_GRN = "\033[32m"
_YLW = "\033[33m"
_CYN = "\033[36m"
_RED = "\033[31m"
_DIM = "\033[2m"


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _print(color: str, tag: str, msg: str) -> None:
    print(f"{color}[{_ts()}][{tag}]{_R} {msg}")


def _banner(msg: str) -> None:
    bar = "─" * 60
    print(f"\n{_BOLD}{_CYN}{bar}")
    print(f"  {msg}")
    print(f"{bar}{_R}\n")


# ── core pipeline ─────────────────────────────────────────────────────────────

class LiveAnalyzer:
    def __init__(
        self,
        cookies: str,
        whisper_model: str,
        chunk_minutes: int,
        output_file: str,
        api_key: str | None,
    ):
        self.cookies = cookies
        self.chunk_seconds = chunk_minutes * 60
        self.output_file = output_file
        self._transcriber = Transcriber(model_size=whisper_model)
        self._summarizer = Summarizer(api_key=api_key)
        self._capture: AudioCapture | None = None

    def stop(self) -> None:
        if self._capture:
            self._capture.stop()

    def _write_output(self, content: str, suffix: str = "") -> None:
        if not self.output_file:
            return
        path = Path(self.output_file)
        if suffix:
            path = path.with_stem(path.stem + suffix)
        path.write_text(content, encoding="utf-8")
        _print(_GRN, "保存", f"已写入 {path}")

    async def _process_chunk(self, wav_path: str) -> None:
        """Transcribe one audio chunk, update rolling summary, print it."""
        _print(_CYN, "转录", f"正在转录第 {self._summarizer.chunk_count + 1} 段音频 …")
        try:
            transcript = await self._transcriber.transcribe_async(wav_path)
        except Exception as exc:
            _print(_RED, "错误", f"转录失败: {exc}")
            return

        if not transcript.strip():
            _print(_YLW, "提示", "该段未检测到语音内容（可能是静音）")
            return

        _print(_CYN, "摘要", "正在更新摘要 …")
        try:
            summary = await self._summarizer.add_chunk(transcript)
        except Exception as exc:
            _print(_RED, "错误", f"摘要更新失败: {exc}")
            return

        _banner(f"阶段摘要（第 {self._summarizer.chunk_count} 段）")
        print(summary)
        print()
        self._write_output(summary, f"_chunk{self._summarizer.chunk_count:02d}")

    async def analyze_stream(self, stream_url: str, owner: str = "", title: str = "") -> None:
        """Capture audio from stream_url and process chunks until stream ends."""
        _print(_GRN, "开始", f"连接直播流: {stream_url[:80]}…")

        self._capture = AudioCapture(
            stream_url=stream_url,
            chunk_seconds=self.chunk_seconds,
            cookies=self.cookies,
        )

        try:
            async for wav_path in self._capture.run():
                await self._process_chunk(wav_path)
        except asyncio.CancelledError:
            _print(_YLW, "中断", "收到中断信号，生成最终报告 …")
        except Exception as exc:
            _print(_RED, "错误", f"录制出错: {exc}")
        finally:
            await self._finish(owner, title)

    async def _finish(self, owner: str, title: str) -> None:
        if not self._summarizer.has_content:
            _print(_YLW, "提示", "未获取到任何内容，无法生成报告。")
            return

        _print(_CYN, "报告", "直播结束，正在生成完整报告 …")
        try:
            report = await self._summarizer.final_report(owner=owner, title=title)
        except Exception as exc:
            _print(_RED, "错误", f"报告生成失败: {exc}")
            return

        _banner("直播完整内容报告")
        print(report)
        self._write_output(report, "_final_report")

    async def watch_user(self, user_id: str, interval: int) -> None:
        checker = DouyinChecker(cookies=self.cookies)

        async def on_live_start(info: LiveInfo) -> None:
            _banner(f"开播检测 ▶  {info.owner} — {info.title}")
            stream_url = info.best_stream_url()
            if not stream_url:
                _print(_RED, "错误", "未能获取直播流地址，跳过本次直播。")
                return
            _print(_GRN, "流地址", stream_url[:80] + "…")
            await self.analyze_stream(stream_url, owner=info.owner, title=info.title)

        async def on_live_end() -> None:
            _print(_YLW, "下播", f"直播结束，恢复监控（每 {interval}s 检查一次）…")

        _print(_GRN, "监控", f"开始监控用户 {user_id}，间隔 {interval}s")
        await checker.watch(user_id, on_live_start=on_live_start,
                            on_live_end=on_live_end, interval=interval)

    async def fetch_room(self, room_id: str) -> None:
        checker = DouyinChecker(cookies=self.cookies)
        _print(_CYN, "查询", f"获取房间 {room_id} 信息 …")
        info = await checker.get_room_info(room_id)

        if info is None:
            _print(_RED, "错误", "无法获取直播间信息，请检查 room_id 和 Cookie。")
            sys.exit(1)

        if not info.is_live:
            _print(_YLW, "提示", f"该直播间当前未开播（状态={info.status}）。")
            sys.exit(0)

        stream_url = info.best_stream_url()
        if not stream_url:
            _print(_RED, "错误", "未能从页面中提取直播流地址。")
            sys.exit(1)

        _banner(f"直播分析 ▶  {info.owner} — {info.title}")
        await self.analyze_stream(stream_url, owner=info.owner, title=info.title)


# ── CLI ───────────────────────────────────────────────────────────────────────

def _common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--cookies", "-c", default="",
                   metavar="STR",
                   help='Cookie 字符串，例如 "ttwid=xxx; sid_tt=yyy"')
    p.add_argument("--cookies-file", "-f", default="",
                   metavar="PATH",
                   help="Cookie 文件（每行 key=value）")
    p.add_argument("--api-key", default=os.environ.get("ANTHROPIC_API_KEY", ""),
                   metavar="KEY",
                   help="Claude API Key（默认读 ANTHROPIC_API_KEY 环境变量）")
    p.add_argument("--whisper-model", default="medium",
                   choices=["tiny", "base", "small", "medium", "large-v3"],
                   metavar="SIZE",
                   help="Whisper 模型大小（默认 medium，首次运行会自动下载）")
    p.add_argument("--chunk-minutes", type=int, default=5,
                   metavar="N",
                   help="每隔多少分钟生成一次阶段摘要（默认 5 分钟）")
    p.add_argument("--output", "-o", default="",
                   metavar="PATH",
                   help="将摘要和报告写入此文件（可选）")
    p.add_argument("--verbose", "-v", action="store_true",
                   help="显示调试日志")


def _resolve_cookies(args: argparse.Namespace) -> str:
    if args.cookies:
        return args.cookies
    if args.cookies_file:
        try:
            text = Path(args.cookies_file).read_text(encoding="utf-8").strip()
            if "\n" in text:
                return "; ".join(
                    line.strip() for line in text.splitlines()
                    if "=" in line and not line.startswith("#")
                )
            return text
        except FileNotFoundError:
            print(f"[错误] Cookie 文件不存在: {args.cookies_file}", file=sys.stderr)
            sys.exit(1)
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="analyzer",
        description="抖音直播内容分析工具 — 自动转录 + AI 摘要",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subs = parser.add_subparsers(dest="command", required=True)

    # watch
    wp = subs.add_parser("watch", help="监控用户，开播时自动分析")
    _common(wp)
    wp.add_argument("--user-id", "-u", required=True, metavar="ID",
                    help="抖音号（短号）或数字 ID")
    wp.add_argument("--interval", "-i", type=int, default=60, metavar="SEC",
                    help="开播检测轮询间隔（秒，默认 60）")

    # fetch
    fp = subs.add_parser("fetch", help="直接分析正在直播的房间")
    _common(fp)
    fp.add_argument("--room-id", "-r", required=True, metavar="ID",
                    help="直播间数字 ID")

    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    cookies = _resolve_cookies(args)
    if not cookies:
        _print(_YLW, "提示", "未提供 Cookie，访问某些直播间可能受限。")

    if not args.api_key:
        _print(_RED, "错误",
               "未找到 Claude API Key。\n"
               "  请设置环境变量: export ANTHROPIC_API_KEY=sk-ant-...\n"
               "  或传入参数:     --api-key sk-ant-...")
        sys.exit(1)

    analyzer = LiveAnalyzer(
        cookies=cookies,
        whisper_model=args.whisper_model,
        chunk_minutes=args.chunk_minutes,
        output_file=args.output,
        api_key=args.api_key or None,
    )

    try:
        if args.command == "watch":
            asyncio.run(analyzer.watch_user(args.user_id, args.interval))
        elif args.command == "fetch":
            asyncio.run(analyzer.fetch_room(args.room_id))
    except KeyboardInterrupt:
        print(f"\n{_YLW}[停止]{_R} 用户中断。")


if __name__ == "__main__":
    main()
