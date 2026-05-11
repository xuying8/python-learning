"""
Live-stream content summarizer powered by Claude.

Two modes:
  rolling  — called after each audio chunk; maintains a compact running
             summary so you always have an up-to-date snapshot.
  final    — called when the stream ends; produces a structured report
             from the full accumulated transcript.
"""
import logging
from datetime import datetime

import anthropic

logger = logging.getLogger(__name__)

_SYSTEM = (
    "你是一个专业的直播内容分析师。"
    "用户会陆续提供一段抖音直播的语音转录文字，"
    "你需要帮助用户理解直播内容，提取关键信息，生成清晰的摘要。"
    "直播转录可能有口语化、不完整的句子，请合理理解并整理。"
)

_ROLLING_TMPL = """\
【最新转录片段】（{timestamp}，第{idx}段）
{transcript}

【当前摘要】
{current_summary}

请根据最新片段更新摘要。要求：
- 新内容优先，旧内容若无变化可保留关键点
- 语言精炼，按话题分条
- 保留数字、产品名、价格、链接等具体信息
- 总长度不超过 400 字
"""

_FINAL_TMPL = """\
以下是一场抖音直播从开始到结束的完整语音转录，按时间顺序排列：

{full_transcript}

请生成一份完整的直播内容报告，结构如下：

## 直播概况
主播 / 标题 / 预估时长 / 核心主题

## 内容摘要
按话题或时间段分章节，每个章节用小标题 + 要点列表

## 重点信息
产品推荐、价格优惠、福利活动、重要链接、数据等

## 总体评价
这场直播最值得关注的 3 条结论

要求：条理清晰，语言简洁，方便快速阅读。
"""


class Summarizer:
    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-4-6"):
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model
        self._current_summary = ""
        self._chunks: list[tuple[str, str]] = []   # (timestamp, transcript)

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    @property
    def has_content(self) -> bool:
        return bool(self._chunks)

    async def add_chunk(self, transcript: str) -> str:
        """
        Add a new transcript chunk, update the rolling summary, and return it.
        Returns the previous summary unchanged if the transcript is empty.
        """
        transcript = transcript.strip()
        if not transcript:
            logger.info("Empty transcript chunk, skipping summarization.")
            return self._current_summary

        timestamp = datetime.now().strftime("%H:%M")
        self._chunks.append((timestamp, transcript))
        idx = len(self._chunks)

        prompt = _ROLLING_TMPL.format(
            timestamp=timestamp,
            idx=idx,
            transcript=transcript,
            current_summary=self._current_summary or "（暂无，这是第一段）",
        )

        logger.info("Sending chunk %d to Claude for rolling summary …", idx)
        resp = await self._client.messages.create(
            model=self._model,
            max_tokens=700,
            system=_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        self._current_summary = resp.content[0].text.strip()
        logger.info("Rolling summary updated (%d chars).", len(self._current_summary))
        return self._current_summary

    async def final_report(self, owner: str = "", title: str = "") -> str:
        """
        Generate a comprehensive structured report from the full transcript.
        Call this once after the stream ends.
        """
        if not self._chunks:
            return "未录制到任何直播内容。"

        full = "\n\n".join(
            f"[{ts} · 第{i+1}段]\n{text}"
            for i, (ts, text) in enumerate(self._chunks)
        )

        context_lines = []
        if owner:
            context_lines.append(f"主播：{owner}")
        if title:
            context_lines.append(f"直播标题：{title}")
        context = "\n".join(context_lines) + "\n\n" if context_lines else ""

        prompt = context + _FINAL_TMPL.format(full_transcript=full)

        logger.info(
            "Generating final report from %d chunks (%d chars total) …",
            len(self._chunks), len(full),
        )
        resp = await self._client.messages.create(
            model=self._model,
            max_tokens=4000,
            system=_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip()
