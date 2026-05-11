"""
Audio capture from a Douyin live stream URL using ffmpeg.

Strategy: run ffmpeg with the segment muxer so it continuously writes
fixed-duration WAV chunks to a temp directory.  A polling loop detects
completed chunks (all but the latest file) and calls on_chunk_ready().
"""
import asyncio
import glob
import logging
import os
import shutil
import tempfile

logger = logging.getLogger(__name__)

_SAMPLE_RATE = 16000   # Hz — required by Whisper


def _check_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg not found. Install it first:\n"
            "  Ubuntu/Debian: sudo apt install ffmpeg\n"
            "  macOS:         brew install ffmpeg\n"
            "  Windows:       https://ffmpeg.org/download.html"
        )


class AudioCapture:
    """
    Captures audio from a live stream URL, emitting WAV file paths as each
    chunk completes.

    Usage::

        cap = AudioCapture(stream_url, chunk_seconds=300)
        async for chunk_path in cap.run():
            # chunk_path is a complete WAV file ready for transcription
            transcript = transcribe(chunk_path)
    """

    def __init__(self, stream_url: str, chunk_seconds: int = 300, cookies: str = ""):
        self.stream_url = stream_url
        self.chunk_seconds = chunk_seconds
        self.cookies = cookies
        self._proc: asyncio.subprocess.Process | None = None
        self._tmpdir: str = ""

    def stop(self) -> None:
        if self._proc and self._proc.returncode is None:
            self._proc.terminate()

    def cleanup(self) -> None:
        if self._tmpdir and os.path.exists(self._tmpdir):
            shutil.rmtree(self._tmpdir, ignore_errors=True)

    async def run(self):
        """
        Async generator that yields completed WAV chunk file paths.
        Cleans up temp directory when done.
        """
        _check_ffmpeg()
        self._tmpdir = tempfile.mkdtemp(prefix="dy_audio_")
        chunk_pattern = os.path.join(self._tmpdir, "chunk_%04d.wav")
        glob_pattern = os.path.join(self._tmpdir, "chunk_*.wav")

        cmd = ["ffmpeg", "-y"]

        # Pass cookies as HTTP headers for authenticated streams
        if self.cookies:
            cmd += ["-headers", f"Cookie: {self.cookies}\r\n"]

        cmd += [
            "-i", self.stream_url,
            "-vn",                           # drop video
            "-acodec", "pcm_s16le",          # raw PCM for Whisper
            "-ar", str(_SAMPLE_RATE),
            "-ac", "1",                      # mono
            "-f", "segment",
            "-segment_time", str(self.chunk_seconds),
            "-segment_format", "wav",
            chunk_pattern,
        ]

        logger.info("Starting ffmpeg (chunk=%ds) …", self.chunk_seconds)
        self._proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )

        processed: set[str] = set()
        try:
            while self._proc.returncode is None:
                await asyncio.sleep(10)
                chunks = sorted(glob.glob(glob_pattern))
                # All but the last segment are complete (ffmpeg is still writing the last)
                complete = chunks[:-1] if len(chunks) > 1 else []
                for path in complete:
                    if path not in processed and os.path.getsize(path) > 0:
                        processed.add(path)
                        logger.info("Chunk ready: %s", os.path.basename(path))
                        yield path

            # ffmpeg exited — process whatever remains
            await asyncio.sleep(1)
            for path in sorted(glob.glob(glob_pattern)):
                if path not in processed and os.path.getsize(path) > 0:
                    processed.add(path)
                    logger.info("Final chunk: %s", os.path.basename(path))
                    yield path

        except asyncio.CancelledError:
            self.stop()
            raise
        finally:
            self.cleanup()

        rc = self._proc.returncode
        if rc not in (0, None, -15):   # -15 = SIGTERM (our own stop())
            stderr = await self._proc.stderr.read()
            logger.warning("ffmpeg exited %s:\n%s", rc, stderr.decode(errors="replace")[-2000:])
