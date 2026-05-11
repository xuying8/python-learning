"""
Douyin live-status checker.

Polls live.douyin.com to detect when a user goes live and extracts the
room metadata (room_id, uid, title, owner) needed for WebSocket connection.
"""
import asyncio
import json
import logging
import re
import urllib.parse
from dataclasses import dataclass, field
from typing import Callable, Awaitable

import httpx

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://live.douyin.com/",
}


@dataclass
class LiveInfo:
    room_id: str
    is_live: bool
    title: str
    owner: str
    uid: str
    status: int  # 2 = live, 4 = offline

    def __str__(self) -> str:
        state = "直播中" if self.is_live else "未开播"
        return f"[{state}] {self.owner} | {self.title} (room_id={self.room_id})"


def _parse_cookies(cookie_str: str) -> dict:
    if not cookie_str:
        return {}
    out = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def _extract_render_data(html: str) -> LiveInfo | None:
    """Parse window.__RENDER_DATA__ from Douyin live page HTML."""
    match = re.search(
        r"window\.__RENDER_DATA__\s*=\s*decodeURIComponent\(\"(.+?)\"\)",
        html,
        re.DOTALL,
    )
    if not match:
        return None
    try:
        raw = urllib.parse.unquote(match.group(1))
        data = json.loads(raw)
        initial = data["app"]["initialState"]
        room = initial["roomStore"]["roomInfo"]["room"]
        uid = str(
            initial.get("userStore", {}).get("odin", {}).get("user_id", "")
        )
        return LiveInfo(
            room_id=str(room.get("id_str") or room.get("id", "")),
            is_live=(room.get("status") == 2),
            title=room.get("title", ""),
            owner=room.get("owner", {}).get("nickname", ""),
            uid=uid,
            status=room.get("status", 4),
        )
    except (KeyError, TypeError, json.JSONDecodeError):
        return None


def _extract_next_data(html: str) -> LiveInfo | None:
    """Parse __NEXT_DATA__ as fallback."""
    match = re.search(
        r'<script id="__NEXT_DATA__"[^>]*>(.+?)</script>', html, re.DOTALL
    )
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
        rooms = (
            data["props"]["pageProps"]
            .get("roomInfoRes", {})
            .get("data", [])
        )
        if not rooms:
            return None
        room = rooms[0].get("room", {})
        return LiveInfo(
            room_id=str(room.get("id_str") or room.get("id", "")),
            is_live=(room.get("status") == 2),
            title=room.get("title", ""),
            owner=room.get("owner", {}).get("nickname", ""),
            uid="",
            status=room.get("status", 4),
        )
    except (KeyError, TypeError, json.JSONDecodeError):
        return None


class DouyinChecker:
    def __init__(self, cookies: str = ""):
        self._cookies = _parse_cookies(cookies)

    async def get_room_info(self, user_id: str) -> LiveInfo | None:
        """
        Fetch live room info for a user (抖音号 or numeric room_id).
        Returns None on network/parse errors.
        """
        url = f"https://live.douyin.com/{user_id}"
        try:
            async with httpx.AsyncClient(
                headers=_HEADERS,
                cookies=self._cookies,
                follow_redirects=True,
                timeout=15,
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("HTTP error fetching room info for %s: %s", user_id, e)
            return None

        info = _extract_render_data(resp.text) or _extract_next_data(resp.text)
        if info is None:
            logger.warning("Could not parse room info from page (user_id=%s)", user_id)
        return info

    async def watch(
        self,
        user_id: str,
        on_live_start: Callable[["LiveInfo"], Awaitable[None]],
        on_live_end: Callable[[], Awaitable[None]] | None = None,
        interval: int = 60,
    ) -> None:
        """
        Poll forever, calling on_live_start(info) when the stream starts and
        on_live_end() when it ends.  on_live_start is awaited (blocks the loop
        while the stream is running), so polling resumes after the stream ends.
        """
        was_live = False
        logger.info("Watching %s every %ds", user_id, interval)

        while True:
            info = await self.get_room_info(user_id)
            if info:
                if info.is_live and not was_live:
                    was_live = True
                    await on_live_start(info)
                elif not info.is_live and was_live:
                    was_live = False
                    if on_live_end:
                        await on_live_end()
            await asyncio.sleep(interval)
