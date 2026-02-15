"""
Тесты генерации пути для аватара (User.upload_to)
==================================================
Проверяет правила формирования пути файла:

  - идентификатор папки: email → phone → "unknown"
  - расширение файла сохраняется
  - имя файла — уникальный UUID (два вызова дают разные пути)
"""

import pytest

from users.models import User


def test_uses_email_as_folder_identifier():
    user = User(email="upload@example.com")
    path = user.upload_to("photo.jpg")
    assert "upload@example.com" in path


@pytest.mark.parametrize("ext", ["jpg", "jpeg", "png", "webp"])
def test_preserves_file_extension(ext):
    user = User(email="ext@example.com")
    path = user.upload_to(f"file.{ext}")
    assert path.endswith(f".{ext}")


def test_falls_back_to_phone_when_no_email():
    user = User(phone="+79001110000")
    path = user.upload_to("avatar.png")
    assert "+79001110000" in path
    assert "unknown" not in path


def test_falls_back_to_unknown_when_no_contact():
    user = User()
    path = user.upload_to("pic.jpeg")
    assert "unknown" in path


def test_uuid_filename_is_unique_per_call():
    user = User(email="uuid@example.com")
    path1 = user.upload_to("file.png")
    path2 = user.upload_to("file.png")
    assert path1 != path2


def test_path_starts_with_avatars_prefix():
    user = User(email="prefix@example.com")
    path = user.upload_to("img.png")
    assert path.startswith("avatars/")
