"""Преобразование ссылок на видео в embed-URL для фронта."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse


def _youtube_embed(url: str) -> str | None:
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower().replace("www.", "")
    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
        return (
            f"https://www.youtube.com/embed/{video_id}" if video_id else None
        )
    if host in ("youtube.com", "m.youtube.com"):
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [None])[0]
            return (
                f"https://www.youtube.com/embed/{video_id}"
                if video_id
                else None
            )
        if parsed.path.startswith("/embed/"):
            return url
        if parsed.path.startswith("/shorts/"):
            video_id = parsed.path.split("/")[2]
            return (
                f"https://www.youtube.com/embed/{video_id}"
                if video_id
                else None
            )
    return None


def _rutube_embed(url: str) -> str | None:
    match = re.search(r"rutube\.ru/video/([a-f0-9-]+)", url, re.I)
    if match:
        return f"https://rutube.ru/play/embed/{match.group(1)}"
    return None


def _vk_embed(url: str) -> str | None:
    match = re.search(r"vk\.com/video(-?\d+)_(\d+)", url)
    if match:
        oid, vid = match.group(1), match.group(2)
        return f"https://vk.com/video_ext.php?oid={oid}&id={vid}"
    return None


def to_embed_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    for fn in (_youtube_embed, _rutube_embed, _vk_embed):
        embed = fn(url)
        if embed:
            return embed
    return url


def build_video_payload(obj, request=None) -> dict | None:
    """Сериализуемое представление видео-объяснения."""
    video_file = getattr(obj, "video_file", None)
    video_url = getattr(obj, "video_url", "") or ""

    if video_file and video_file.name:
        try:
            file_url = video_file.url
        except ValueError:
            file_url = ""
        if file_url:
            if request and not file_url.startswith(("http://", "https://")):
                file_url = request.build_absolute_uri(file_url)
            return {
                "kind": "file",
                "url": file_url,
                "embed_url": file_url,
            }

    video_url = video_url.strip()
    if video_url:
        return {
            "kind": "embed",
            "url": video_url,
            "embed_url": to_embed_url(video_url),
        }
    return None
