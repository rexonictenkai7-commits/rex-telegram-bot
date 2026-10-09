import asyncio
import os
import subprocess
import shlex
from typing import Optional
from config import TEMP_DIR


async def run_ffmpeg(cmd: list, timeout: int = 600) -> str:
    """Run ffmpeg command, return stdout+stderr on failure."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise RuntimeError("FFmpeg timed out")
    if proc.returncode != 0:
        err = (stderr or b"").decode(errors="ignore")[-1500:]
        raise RuntimeError(f"FFmpeg error:\n{err}")
    return (stdout or b"").decode(errors="ignore")


def _out_path(inp: str, suffix: str) -> str:
    base = os.path.splitext(os.path.basename(inp))[0]
    return os.path.join(TEMP_DIR, f"{base}_{suffix}.mp3")


async def change_speed(input_path: str, speed: float = 1.25) -> str:
    """Change tempo without changing pitch (uses atempo)."""
    out = _out_path(input_path, f"speed{speed}")
    # atempo accepts 0.5-2.0; chain if needed
    filters = []
    s = speed
    while s > 2.0:
        filters.append("atempo=2.0")
        s /= 2.0
    while s < 0.5:
        filters.append("atempo=0.5")
        s /= 0.5
    filters.append(f"atempo={s:.4f}")
    af = ",".join(filters)
    cmd = ["ffmpeg", "-y", "-i", input_path, "-filter:a", af, "-vn", out]
    await run_ffmpeg(cmd)
    return out


async def change_pitch(input_path: str, semitones: float = 2.0) -> str:
    """Pitch shift using asetrate + aresample (simple, quality ok)."""
    out = _out_path(input_path, f"pitch{semitones}")
    factor = 2 ** (semitones / 12.0)
    # asetrate changes pitch+speed, then atempo corrects speed
    af = f"asetrate=44100*{factor:.6f},aresample=44100,atempo={1/factor:.6f}"
    cmd = ["ffmpeg", "-y", "-i", input_path, "-filter:a", af, "-vn", out]
    await run_ffmpeg(cmd)
    return out


async def bass_boost(input_path: str, gain: float = 8.0) -> str:
    out = _out_path(input_path, "bass")
    af = f"bass=g={gain}:f=100:w=0.5"
    cmd = ["ffmpeg", "-y", "-i", input_path, "-filter:a", af, "-vn", out]
    await run_ffmpeg(cmd)
    return out


async def change_volume(input_path: str, db: float = 5.0) -> str:
    out = _out_path(input_path, f"vol{db}")
    af = f"volume={db}dB"
    cmd = ["ffmpeg", "-y", "-i", input_path, "-filter:a", af, "-vn", out]
    await run_ffmpeg(cmd)
    return out


async def reverse_audio(input_path: str) -> str:
    out = _out_path(input_path, "reverse")
    cmd = ["ffmpeg", "-y", "-i", input_path, "-filter:a", "areverse", "-vn", out]
    await run_ffmpeg(cmd)
    return out


async def nightcore(input_path: str) -> str:
    """Classic nightcore: speed up + pitch up."""
    out = _out_path(input_path, "nightcore")
    # ~1.25 speed + ~3-4 semitones feel
    af = "asetrate=44100*1.25,aresample=44100,atempo=1.0"
    cmd = ["ffmpeg", "-y", "-i", input_path, "-filter:a", af, "-vn", out]
    await run_ffmpeg(cmd)
    return out


async def vaporwave(input_path: str) -> str:
    out = _out_path(input_path, "vaporwave")
    af = "asetrate=44100*0.8,aresample=44100,atempo=1.0,bass=g=5"
    cmd = ["ffmpeg", "-y", "-i", input_path, "-filter:a", af, "-vn", out]
    await run_ffmpeg(cmd)
    return out


async def auto_funk(input_path: str) -> str:
    """Simple auto-funk: mild speed up, bass boost, slight pitch."""
    out = _out_path(input_path, "funk")
    af = "asetrate=44100*1.08,aresample=44100,atempo=1.0,bass=g=6:f=110,treble=g=2"
    cmd = ["ffmpeg", "-y", "-i", input_path, "-filter:a", af, "-vn", out]
    await run_ffmpeg(cmd)
    return out


async def basic_vocal_remove(input_path: str) -> str:
    """
    Simple center-channel vocal removal (karaoke style).
    Works best on stereo tracks where vocals are centered.
    For high quality use Demucs (optional heavy dependency).
    """
    out = _out_path(input_path, "instrumental")
    # Classic karaoke filter
    af = "pan=stereo|c0=c0-c1|c1=c1-c0"
    cmd = ["ffmpeg", "-y", "-i", input_path, "-filter:a", af, "-vn", out]
    await run_ffmpeg(cmd)
    return out


async def extract_vocals_basic(input_path: str) -> str:
    """Rough vocal extract (opposite of karaoke)."""
    out = _out_path(input_path, "vocals")
    af = "pan=mono|c0=0.5*c0+-0.5*c1"
    cmd = ["ffmpeg", "-y", "-i", input_path, "-filter:a", af, "-ac", "1", "-vn", out]
    await run_ffmpeg(cmd)
    return out


async def try_demucs_vocal_remove(input_path: str) -> Optional[str]:
    """Try Demucs if installed. Returns path to instrumental or None."""
    try:
        import demucs.separate
        # demucs CLI style via subprocess is more reliable
        out_dir = os.path.join(TEMP_DIR, "demucs_out")
        os.makedirs(out_dir, exist_ok=True)
        cmd = [
            "python", "-m", "demucs",
            "--two-stems", "vocals",
            "-n", "htdemucs",
            "-o", out_dir,
            input_path,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await asyncio.wait_for(proc.communicate(), timeout=900)
        if proc.returncode != 0:
            return None
        # Find no_vocals / instrumental
        for root, _, files in os.walk(out_dir):
            for f in files:
                if "no_vocals" in f or "instrumental" in f.lower():
                    return os.path.join(root, f)
        return None
    except Exception:
        return None


# Preset map for /edit buttons
EFFECT_PRESETS = {
    "bass_boost": ("Bass Boost", bass_boost),
    "speed_up": ("Speed 1.25x", lambda p: change_speed(p, 1.25)),
    "slow_down": ("Slow 0.8x", lambda p: change_speed(p, 0.8)),
    "pitch_up": ("Pitch +2", lambda p: change_pitch(p, 2)),
    "pitch_down": ("Pitch -2", lambda p: change_pitch(p, -2)),
    "volume_up": ("Volume +5dB", lambda p: change_volume(p, 5)),
    "reverse": ("Reverse", reverse_audio),
    "nightcore": ("Nightcore", nightcore),
    "vaporwave": ("Vaporwave", vaporwave),
    "funk": ("Auto Funk", auto_funk),
}


async def get_duration(path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    out, _ = await proc.communicate()
    try:
        return float(out.decode().strip())
    except Exception:
        return 0.0
