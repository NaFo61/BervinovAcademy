from unittest.mock import patch

from django.db.models.signals import post_save
import pytest

from translations.models import TranslationMemory
from translations.signals import apply_translation_to_model


@pytest.fixture(autouse=True, scope="session")
def disconnect_translation_before_tests():
    post_save.disconnect(apply_translation_to_model, sender=TranslationMemory)
    with patch(
        "translations.services.TranslationService.get_translation"
    ) as mock_get:
        mock_get.return_value = "test_translation"

        yield

    post_save.connect(apply_translation_to_model, sender=TranslationMemory)
