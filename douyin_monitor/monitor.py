#!/usr/bin/env python3
"""
抖音直播监控工具
================

用法示例
--------
# 监控某用户，开播时自动抓取直播内容:
  python monitor.py watch --user-id 123456 --cookies "ttwid=xxx; sid_tt=yyy"

# 直接连接正在直播的房间 (填数字 room_id):
  python monitor.py fetch --room-id 7234567890123 --cookies "ttwid=xxx; sid_tt=yyy"

# 将内容写入日志文件，同时显示进场消息和统计:
  python monitor.py watch --user-id 123456 \\
      --cookies "ttwid=xxx" --log-file live.log --show-stats

如何获取 Cookie
---------------
1. 打开浏览器，访问 https://live.douyin.com 并登录
2. 按 F12 -> Application -> Cookies -> https://live.douyin.com
3. 复制 ttwid 的值，以及 sid_tt（可选但推荐）
4. 传入: --cookies "ttwid=<value>; sid_tt=<value>"
   或保存到文件每行 key=value，用 --cookies-file 加载
"""
import argparse
import asyncio
import logging
import sys
from datetime import datetime

from checker import DouyinChecker, LiveInfo
from fetcher import DouyinFetcher

# ---------------------------------------------------------------------------
# Terminal colors
# ---------------------------------------------------------------------------
_R = "\033[0m"
_BOLD = "\033[1m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"
_MAGENTA = "\033[35m"
_BLUE = "\033[34m"
_RED = "\033[31m"
_DIM = "\033[2m"

_EVENT_COLOR = {
    "chat":    _R,
    "gift":    _YELLOW,
    "like":    _MAGENTA,
    "member":  _CYAN,
    "stats":   _BLUE + _DIM,
    "control": _RED + _BOLD,
    "social":  _GREEN,
    "live_start": _BOLD + _GREEN,
    "live_end":   _BOLD + _RED,
}
_EVENT_LABEL = {
    "chat":    "弹幕",
    "gift":    "礼物",
    "like":    "点赞",
    "member":  "进入",
    "stats":   "数据",
    "control": "控制",
    "social":  "互动",
    "live_start": "开播",
    "live_end":   "下播",
}


def _fmt(event: dict) -> str:
    t = event["type"]
    ts = datetime.now().strftime("%H:%M:%S")
    label = _EVENT_LABEL.get(t, t.upper())
    color = _EVENT_COLOR.get(t, _R)

    if t == "chat":
        body = f"{event['user']['nickname']}: {event['content']}"
    elif t == "gift":
        combo = event.get("combo_count") or event.get("count", 1)
        body = f"{event['user']['nickname']} 送出 {event['gift_name']} x{combo}"
    elif t == "like":
        body = f"{event['user']['nickname']} 点了赞  (累计 {event['total']:,})"
    elif t == "member":
        cnt = event.get("member_count", 0)
        body = f"{event['user']['nickname']} 进入直播间" + (f"  (在线 {cnt:,})" if cnt else "")
    elif t == "stats":
        body = f"当前在线: {event['total']:,}"
    elif t == "control":
        body = "直播已结束" if event.get("status") == 3 else f"状态={event.get('status')}"
    elif t == "social":
        action_text = "分享了直播" if event.get("action") == 3 else "关注了主播"
        body = f"{event['user']['nickname']} {action_text}"
    elif t == "live_start":
        body = f"【{event.get('owner', '')}】开播  {event.get('title', '')}"
    elif t == "live_end":
        body = "直播已结束，继续等待下次开播 …"
    else:
        body = str(event)

    return f"{color}[{ts}][{label}] {body}{_R}"


# ---------------------------------------------------------------------------
# Monitor orchestrator
# ---------------------------------------------------------------------------

class Monitor:
    def __init__(
        self,
        cookies: str,
        log_file: str = "",
        show_likes: bool = False,
        show_joins: bool = True,
        show_stats: bool = False,
    ):
        self.cookies = cookies
        self.log_file = log_file
        self.show_likes = show_likes
        self.show_joins = show_joins
        self.show_stats = show_stats
        self._log_fh = None
        self._fetcher = DouyinFetcher()

    def __enter__(self):
        if self.log_file:
            self._log_fh = open(self.log_file, "a", encoding="utf-8")
        return self

    def __exit__(self, *_):
        if self._log_fh:
            self._log_fh.close()

    def _emit(self, event: dict) -> None:
        t = event["type"]
        if t == "like" and not self.show_likes:
            return
        if t == "member" and not self.show_joins:
            return
        if t == "stats" and not self.show_stats:
            return

        line = _fmt(event)
        print(line)

        if self._log_fh:
            self._log_fh.write(
                f"[{datetime.now().isoformat()}] {t.upper()} | {event}\n"
            )
            self._log_fh.flush()

    async def fetch_room(self, room_id: str, uid: str = "") -> None:
        await self._fetcher.start(
            room_id=room_id,
            uid=uid,
            cookies=self.cookies,
            on_event=self._emit,
        )

    async def watch_user(self, user_id: str, interval: int = 60) -> None:
        checker = DouyinChecker(cookies=self.cookies)

        async def on_live_start(info: LiveInfo) -> None:
            self._emit(
                {"type": "live_start", "owner": info.owner, "title": info.title}
            )
            await self.fetch_room(info.room_id, info.uid)

        async def on_live_end() -> None:
            self._emit({"type": "live_end"})

        await checker.watch(
            user_id,
            on_live_start=on_live_start,
            on_live_end=on_live_end,
            interval=interval,
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _common_args(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--cookies", "-c", default="",
        metavar="STR",
        help='Cookie 字符串，例如 "ttwid=xxx; sid_tt=yyy"',
    )
    p.add_argument(
        "--cookies-file", "-f", default="",
        metavar="PATH",
        help="Cookie 文件路径（每行 key=value，或 Netscape 格式）",
    )
    p.add_argument(
        "--log-file", "-l", default="",
        metavar="PATH",
        help="同时将所有事件追加写入此文件",
    )
    p.add_argument(
        "--show-likes", action="store_true",
        help="显示点赞消息（默认隐藏，量大）",
    )
    p.add_argument(
        "--no-joins", action="store_true",
        help="隐藏用户进场消息",
    )
    p.add_argument(
        "--show-stats", action="store_true",
        help="显示在线人数统计",
    )
    p.add_argument(
        "--verbose", "-v", action="store_true",
        help="输出调试日志",
    )


def _load_cookies(args: argparse.Namespace) -> str:
    if args.cookies:
        return args.cookies
    if args.cookies_file:
        try:
            with open(args.cookies_file, encoding="utf-8") as fh:
                content = fh.read().strip()
            if "\n" in content:
                return "; ".join(
                    line.strip()
                    for line in content.splitlines()
                    if "=" in line and not line.startswith("#")
                )
            return content
        except FileNotFoundError:
            print(f"[错误] Cookie 文件不存在: {args.cookies_file}", file=sys.stderr)
            sys.exit(1)
    return ""


async def _cmd_watch(args: argparse.Namespace) -> None:
    cookies = _load_cookies(args)
    print(f"{_BOLD}{_GREEN}[开播监控]{_R} 正在监控用户: {args.user_id}")
    print(f"  检查间隔: {args.interval} 秒")
    if not cookies:
        print(f"  {_YELLOW}提示: 未提供 Cookie，可能无法访问部分直播间{_R}")
    if args.log_file:
        print(f"  日志文件: {args.log_file}")
    print()

    with Monitor(
        cookies=cookies,
        log_file=args.log_file,
        show_likes=args.show_likes,
        show_joins=not args.no_joins,
        show_stats=args.show_stats,
    ) as monitor:
        await monitor.watch_user(args.user_id, interval=args.interval)


async def _cmd_fetch(args: argparse.Namespace) -> None:
    cookies = _load_cookies(args)
    print(f"{_BOLD}{_GREEN}[直播监控]{_R} 连接房间: {args.room_id}")
    if not cookies:
        print(f"  {_YELLOW}提示: 未提供 Cookie，可能无法访问部分直播间{_R}")
    if args.log_file:
        print(f"  日志文件: {args.log_file}")
    print()

    checker = DouyinChecker(cookies=cookies)
    info = await checker.get_room_info(args.room_id)
    uid = info.uid if info else ""

    with Monitor(
        cookies=cookies,
        log_file=args.log_file,
        show_likes=args.show_likes,
        show_joins=not args.no_joins,
        show_stats=args.show_stats,
    ) as monitor:
        await monitor.fetch_room(args.room_id, uid)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="monitor",
        description="抖音直播监控工具 — 开播检测 + 弹幕/礼物/数据实时抓取",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subs = parser.add_subparsers(dest="command", required=True)

    # --- watch ---
    wp = subs.add_parser("watch", help="监控用户，开播时自动连接")
    _common_args(wp)
    wp.add_argument(
        "--user-id", "-u", required=True,
        metavar="ID",
        help="抖音号 (短号) 或直播间数字 ID",
    )
    wp.add_argument(
        "--interval", "-i", type=int, default=60,
        metavar="SEC",
        help="轮询间隔秒数（默认 60）",
    )

    # --- fetch ---
    fp = subs.add_parser("fetch", help="直接连接正在直播的房间")
    _common_args(fp)
    fp.add_argument(
        "--room-id", "-r", required=True,
        metavar="ID",
        help="直播间数字 ID",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        if args.command == "watch":
            asyncio.run(_cmd_watch(args))
        elif args.command == "fetch":
            asyncio.run(_cmd_fetch(args))
    except KeyboardInterrupt:
        print(f"\n{_YELLOW}[停止]{_R} 用户中断，退出监控。")


if __name__ == "__main__":
    main()
