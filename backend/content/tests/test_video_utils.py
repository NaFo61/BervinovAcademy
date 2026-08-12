"""Тесты video_utils: embed URL и file payload."""

from content.video_utils import build_video_payload, to_embed_url


def test_youtube_watch_to_embed():
    assert (
        to_embed_url("https://www.youtube.com/watch?v=abc123XYZ")
        == "https://www.youtube.com/embed/abc123XYZ"
    )


def test_build_video_payload_from_url():
    class Obj:
        video_url = "https://www.youtube.com/watch?v=test1234"
        video_file = None

    payload = build_video_payload(Obj())
    assert payload["kind"] == "embed"
    assert "embed" in payload["embed_url"]


def test_build_video_payload_empty():
    class Obj:
        video_url = ""
        video_file = None

    assert build_video_payload(Obj()) is None


def test_build_video_payload_relative_file_uses_request():
    class FakeFile:
        name = "lessons/a.mp4"
        url = "/media/lessons/a.mp4"

    class Obj:
        video_url = ""
        video_file = FakeFile()

    class Req:
        def build_absolute_uri(self, path):
            return f"https://academy.example{path}"

    payload = build_video_payload(Obj(), Req())
    assert payload["kind"] == "file"
    assert payload["url"] == "https://academy.example/media/lessons/a.mp4"


def test_build_video_payload_s3_signed_url_left_as_is():
    class FakeFile:
        name = "media/lessons/a.mp4"
        url = (
            "https://bervinov-academy-videos.s3.ru-6.storage.selcloud.ru/"
            "media/lessons/a.mp4?X-Amz-Signature=abc"
        )

    class Obj:
        video_url = ""
        video_file = FakeFile()

    payload = build_video_payload(Obj())
    assert payload["url"].startswith("https://bervinov-academy-videos.")
    assert "X-Amz-Signature" in payload["url"]
