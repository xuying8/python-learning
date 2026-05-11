"""
Douyin live WebSocket fetcher.

Connects to a live room's push server, receives protobuf-encoded events
(chat, gifts, likes, members joining, viewer stats, room control), and
dispatches them via a callback.

WebSocket flow:
  1. Build URL with room_id + browser fingerprint params
  2. Connect with valid Douyin cookies (ttwid is the key one)
  3. For each binary frame: decode PushFrame -> (maybe gzip) -> Response -> events
  4. Echo an ACK frame when Response.need_ack is True
  5. The server also sends WebSocket-level pings; websockets handles those
"""
import asyncio
import logging
import random
import urllib.parse
from typing import Callable

from websockets.asyncio.client import connect as ws_connect
from websockets.exceptions import ConnectionClosed

from proto_utils import process_ws_message, build_ack_frame

logger = logging.getLogger(__name__)

_WS_BASE = "wss://webcast3-ws-web-lf.douyin.com/webcast/im/push/v2/"

_BROWSER_PARAMS = {
    "app_name": "douyin_web",
    "version_code": "180800",
    "webcast_sdk_version": "1.3.0",
    "insert_task_id": "",
    "live_id": "1",
    "did_rule": "3",
    "debug": "false",
    "endpoint": "live_pc",
    "support_wrds": "0",
    "im_path": "/webcast/im/fetch/",
    "device_platform": "web",
    "cookie_enabled": "true",
    "screen_width": "1536",
    "screen_height": "864",
    "browser_language": "zh-CN",
    "browser_platform": "Win32",
    "browser_name": "Mozilla",
    "browser_version": (
        "5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "browser_online": "true",
    "tz_name": "Asia/Shanghai",
    "host": "https://live.douyin.com",
    "aid": "6383",
}

_WS_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Origin": "https://live.douyin.com",
    "Referer": "https://live.douyin.com/",
}


def _build_ws_url(
    room_id: str,
    uid: str,
    cursor: str = "",
    internal_ext: str = "",
) -> str:
    params = {
        **_BROWSER_PARAMS,
        "user_unique_id": uid or str(random.randint(10**18, 10**19 - 1)),
        "room_id": room_id,
        "cursor": cursor,
        "internal_ext": internal_ext,
    }
    return _WS_BASE + "?" + urllib.parse.urlencode(params)


class DouyinFetcher:
    def __init__(self) -> None:
        self._running = False

    def stop(self) -> None:
        self._running = False

    async def start(
        self,
        room_id: str,
        uid: str = "",
        cookies: str = "",
        on_event: Callable[[dict], None] | None = None,
        on_disconnect: Callable[[], None] | None = None,
    ) -> None:
        """
        Connect to live room `room_id` and stream events until the stream
        ends or the connection drops.

        on_event(event) is called synchronously for each event dict.
        event['type'] is one of: chat | gift | like | member | stats |
                                  control | social
        """
        self._running = True
        internal_ext = ""
        cursor = ""

        extra_headers = dict(_WS_HEADERS)
        if cookies:
            extra_headers["Cookie"] = cookies

        ws_url = _build_ws_url(room_id, uid, cursor, internal_ext)
        logger.info("Connecting to room %s …", room_id)

        try:
            async with ws_connect(
                ws_url,
                additional_headers=extra_headers,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=5,
            ) as ws:
                logger.info("Connected to room %s", room_id)

                async for raw_msg in ws:
                    if not isinstance(raw_msg, bytes):
                        continue
                    try:
                        need_ack, log_id, new_ext, events = process_ws_message(raw_msg)
                    except Exception as exc:
                        logger.debug("Failed to parse frame: %s", exc)
                        continue

                    if new_ext:
                        internal_ext = new_ext

                    if need_ack and log_id:
                        try:
                            await ws.send(build_ack_frame(log_id))
                        except Exception:
                            pass

                    if on_event:
                        for event in events:
                            on_event(event)
                            # Control message status=3 means stream ended
                            if event["type"] == "control" and event.get("status") == 3:
                                logger.info("Stream ended (server control message)")
                                self._running = False

                    if not self._running:
                        await ws.close()
                        break

        except ConnectionClosed as exc:
            logger.info("WebSocket closed: %s", exc)
        except Exception as exc:
            logger.error("WebSocket error: %s", exc)
        finally:
            self._running = False
            if on_disconnect:
                on_disconnect()
