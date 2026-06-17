from content.video_utils import build_video_payload, to_embed_url


def test_youtube_watch_to_embed():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert to_embed_url(url) == "https://www.youtube.com/embed/dQw4w9WgXcQ"


def test_youtube_short_to_embed():
    url = "https://youtu.be/abc123XYZ"
    assert to_embed_url(url) == "https://www.youtube.com/embed/abc123XYZ"


def test_build_video_payload_from_url():
    class Obj:
        video_url = "https://www.youtube.com/watch?v=test1234"
        video_file = None

    payload = build_video_payload(Obj())
    assert payload["kind"] == "embed"
    assert "embed/test1234" in payload["embed_url"]


def test_build_video_payload_empty():
    class Obj:
        video_url = ""
        video_file = None

    assert build_video_payload(Obj()) is None
