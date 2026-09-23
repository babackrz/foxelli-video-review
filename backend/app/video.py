import math
import json
import re
import subprocess


MAX_BYTES = 250 * 1024 * 1024
MAX_SECONDS = 180


def duration_seconds(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type:format=duration", "-of", "json", str(path)],
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )
    probe = json.loads(result.stdout)
    if not any(stream.get("codec_type") == "video" for stream in probe.get("streams", [])):
        raise ValueError("MP4 has no video stream")
    duration = float(probe["format"]["duration"])
    if not math.isfinite(duration) or duration <= 0 or duration > MAX_SECONDS:
        raise ValueError("Video must be at most 3 minutes long")
    return math.ceil(duration)


def valid_second(second, duration):
    return isinstance(second, int) and not isinstance(second, bool) and 0 <= second < duration


def post_requested(prompt):
    return bool(re.search(r"\b(post|add|leave|write|create|put)\b.{0,80}\b(comments?|notes?|feedback)\b", prompt, re.I))
