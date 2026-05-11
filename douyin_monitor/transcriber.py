"""
Speech-to-text transcription using faster-whisper.

faster-whisper is a reimplementation of OpenAI Whisper that runs ~4× faster
with the same accuracy by using CTranslate2 as the backend.

Install: pip install faster-whisper
Models are downloaded automatically on first use:
  tiny   ~75 MB  — fastest, rough accuracy
  base   ~150 MB — decent for testing
  small  ~500 MB — good balance
  medium ~1.5 GB — recommended for Chinese (default)
  large-v3 ~3 GB — highest accuracy
"""
import asyncio
import logging
import os

logger = logging.getLogger(__name__)


class Transcriber:
    def __init__(self, model_size: str = "medium", device: str = "cpu"):
        self._model_size = model_size
        self._device = device
        self._model = None

    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise RuntimeError(
                "faster-whisper is not installed.\n"
                "Run: pip install faster-whisper"
            )
        logger.info(
            "Loading Whisper model '%s' on %s (first run downloads the model) …",
            self._model_size, self._device,
        )
        self._model = WhisperModel(
            self._model_size,
            device=self._device,
            compute_type="int8",    # int8 quantisation — fast on CPU, minimal quality loss
        )
        logger.info("Whisper model ready.")

    def transcribe_file(self, audio_path: str) -> str:
        """
        Transcribe a WAV/MP3/M4A file and return plain text.
        Automatically skips silent sections via VAD filter.
        """
        self._load()
        size_mb = os.path.getsize(audio_path) / 1024 / 1024
        logger.info("Transcribing %s (%.1f MB) …", os.path.basename(audio_path), size_mb)

        segments, info = self._model.transcribe(
            audio_path,
            language="zh",       # assume Mandarin; set None for auto-detect
            beam_size=5,
            vad_filter=True,     # skip silence — keeps transcript cleaner
            vad_parameters={"min_silence_duration_ms": 500},
        )

        text = " ".join(seg.text.strip() for seg in segments if seg.text.strip())
        logger.info(
            "Transcribed %.1fs of audio → %d chars (lang=%s, prob=%.2f)",
            info.duration, len(text), info.language, info.language_probability,
        )
        return text

    async def transcribe_async(self, audio_path: str) -> str:
        """Non-blocking wrapper — runs transcription in a thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.transcribe_file, audio_path)
