"""
Pure-Python protobuf decoder/encoder for Douyin live stream messages.
No external protobuf library required — handles varint, length-delimited,
32-bit and 64-bit wire types.

Douyin WebSocket message hierarchy:
  raw bytes -> PushFrame -> (gzip decompress) -> Response -> []Message
  each Message.method -> ChatMessage | GiftMessage | LikeMessage | ...
"""
import gzip
import struct


# ---------------------------------------------------------------------------
# Low-level encode / decode
# ---------------------------------------------------------------------------

def _decode_varint(data: bytes, pos: int) -> tuple[int, int]:
    result, shift = 0, 0
    while pos < len(data):
        byte = data[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            return result, pos
        shift += 7
    raise ValueError("Unterminated varint")


def _encode_varint(value: int) -> bytes:
    out = []
    while value > 0x7F:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value & 0x7F)
    return bytes(out)


def decode_message(data: bytes) -> dict:
    """Decode protobuf binary into {field_num: value | [value, ...]}."""
    data = bytes(data)
    fields: dict = {}
    pos = 0
    while pos < len(data):
        try:
            tag, pos = _decode_varint(data, pos)
        except (ValueError, IndexError):
            break
        field_num = tag >> 3
        wire_type = tag & 0x7
        try:
            if wire_type == 0:
                value, pos = _decode_varint(data, pos)
            elif wire_type == 1:
                value = struct.unpack_from("<Q", data, pos)[0]
                pos += 8
            elif wire_type == 2:
                length, pos = _decode_varint(data, pos)
                value = data[pos : pos + length]
                pos += length
            elif wire_type == 5:
                value = struct.unpack_from("<I", data, pos)[0]
                pos += 4
            else:
                break
        except (struct.error, ValueError, IndexError):
            break
        if field_num in fields:
            existing = fields[field_num]
            if isinstance(existing, list):
                existing.append(value)
            else:
                fields[field_num] = [existing, value]
        else:
            fields[field_num] = value
    return fields


def _s(fields: dict, num: int, default: str = "") -> str:
    v = fields.get(num)
    if v is None:
        return default
    if isinstance(v, list):
        v = v[0]
    return v.decode("utf-8", errors="replace") if isinstance(v, bytes) else str(v)


def _i(fields: dict, num: int, default: int = 0) -> int:
    v = fields.get(num, default)
    if isinstance(v, list):
        return v[0] if v else default
    return v if v is not None else default


def _b(fields: dict, num: int, default: bytes = b"") -> bytes:
    v = fields.get(num, default)
    if isinstance(v, list):
        return v[0] if v else default
    return v if v is not None else default


def _lst(fields: dict, num: int) -> list:
    v = fields.get(num)
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


# ---------------------------------------------------------------------------
# PushFrame / Response
# ---------------------------------------------------------------------------

def parse_push_frame(data: bytes) -> dict:
    f = decode_message(data)
    return {
        "seq_id": _i(f, 1),
        "log_id": _i(f, 2),
        "payload_encoding": _s(f, 6),
        "payload_type": _s(f, 7),
        "payload": _b(f, 8),
    }


def build_ack_frame(log_id: int) -> bytes:
    """Encode the ACK PushFrame that must be echoed back to the server."""
    type_field = _encode_varint((7 << 3) | 2) + _encode_varint(3) + b"ack"
    log_bytes = str(log_id).encode()
    data_field = _encode_varint((8 << 3) | 2) + _encode_varint(len(log_bytes)) + log_bytes
    return type_field + data_field


def parse_response(data: bytes) -> dict:
    f = decode_message(data)
    messages = []
    for msg_data in _lst(f, 1):
        mf = decode_message(msg_data)
        messages.append({
            "method": _s(mf, 1),
            "payload": _b(mf, 2),
            "msg_id": _i(mf, 3),
        })
    return {
        "messages": messages,
        "need_ack": bool(_i(f, 9)),
        "internal_ext": _s(f, 5),
        "fetch_interval": _i(f, 3),
    }


# ---------------------------------------------------------------------------
# Message-type parsers
# ---------------------------------------------------------------------------

def _decode_user(data: bytes) -> dict:
    if not data:
        return {"id": 0, "nickname": "未知用户"}
    f = decode_message(data)
    return {"id": _i(f, 1), "nickname": _s(f, 3, "未知用户")}


def parse_chat(data: bytes) -> dict:
    f = decode_message(data)
    return {"user": _decode_user(_b(f, 2)), "content": _s(f, 3)}


def parse_gift(data: bytes) -> dict:
    f = decode_message(data)
    gf = decode_message(_b(f, 8)) if f.get(8) else {}
    return {
        "user": _decode_user(_b(f, 7)),
        "gift_name": _s(gf, 15, "未知礼物"),
        "gift_id": _i(f, 2),
        "count": max(_i(f, 5), 1),
        "combo_count": _i(f, 6),
        "repeat_end": bool(_i(f, 14)),
    }


def parse_like(data: bytes) -> dict:
    f = decode_message(data)
    return {
        "user": _decode_user(_b(f, 5)),
        "count": _i(f, 2),
        "total": _i(f, 3),
    }


def parse_member(data: bytes) -> dict:
    f = decode_message(data)
    return {
        "user": _decode_user(_b(f, 2)),
        "member_count": _i(f, 3),
    }


def parse_stats(data: bytes) -> dict:
    f = decode_message(data)
    return {"total": _i(f, 3)}


def parse_control(data: bytes) -> dict:
    # status=3 means the stream ended
    f = decode_message(data)
    return {"status": _i(f, 2)}


def parse_social(data: bytes) -> dict:
    f = decode_message(data)
    return {"user": _decode_user(_b(f, 2)), "action": _i(f, 4)}


_PARSERS = {
    "WebcastChatMessage":        ("chat",    parse_chat),
    "WebcastGiftMessage":        ("gift",    parse_gift),
    "WebcastLikeMessage":        ("like",    parse_like),
    "WebcastMemberMessage":      ("member",  parse_member),
    "WebcastRoomUserSeqMessage": ("stats",   parse_stats),
    "WebcastControlMessage":     ("control", parse_control),
    "WebcastSocialMessage":      ("social",  parse_social),
}


# ---------------------------------------------------------------------------
# Top-level processor
# ---------------------------------------------------------------------------

def process_ws_message(raw: bytes) -> tuple[bool, int, str, list[dict]]:
    """
    Decode one raw WebSocket binary frame from Douyin live.

    Returns (need_ack, log_id, internal_ext, events).
    events is a list of dicts — each has a 'type' key plus message fields.
    """
    frame = parse_push_frame(raw)
    payload = frame["payload"]
    if frame["payload_encoding"] == "gzip":
        payload = gzip.decompress(payload)

    response = parse_response(payload)
    events: list[dict] = []
    for msg in response["messages"]:
        method = msg["method"]
        if method in _PARSERS:
            event_type, parser = _PARSERS[method]
            try:
                event = parser(msg["payload"])
                event["type"] = event_type
                events.append(event)
            except Exception:
                pass

    return (
        response["need_ack"],
        frame["log_id"],
        response["internal_ext"],
        events,
    )
