import logging

from langdetect import DetectorFactory

from translations.services import TranslationService

DetectorFactory.seed = 0
logger = logging.getLogger(__name__)


class AutoTranslateMixin:
    languages = ["ru", "en"]
    translatable_fields: list[str] = []

    # def detect_lang(self, text):
    #     """Определяем язык только исходного текста"""
    #     if not text:
    #         return None
    #
    #     try:
    #         lang = detect(text)
    #         if lang in ["ru", "uk", "be"]:
    #             return "ru"
    #         return "en"
    #     except LangDetectException:
    #         if any(ch in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
    #         for ch in text.lower()):
    #             return "ru"
    #         return "en"

    def detect_lang(self, text):
        """Определение языка без ошибок langdetect"""

        if not text or not text.strip():
            return "en"

        text_lower = text.lower()

        # Если есть кириллица → точно русский
        if any("а" <= ch <= "я" or ch in "ё" for ch in text_lower):
            return "ru"

        # Если есть буквы латиницы → английский
        if any("a" <= ch <= "z" for ch in text_lower):
            return "en"

        # Фолбэк, если ни кириллицы, ни латиницы
        # (редко, но пусть будет)
        return "en"

    def auto_translate_fields(self):
        """
        Проверяет какие поля были изменены вручную (без циклов):
        - Если пользователь изменил title → переводим только title_ru/title_en
        - НЕ переводим обратно, НЕ переведём перевод снова.
        """
        logger.warning(f"99 {self}")

        for base_field in self.translatable_fields:
            # какие именно поля существуют: base_ru, base_en
            ru_field = f"{base_field}_ru"
            en_field = f"{base_field}_en"

            # достаём значения
            val_ru = getattr(self, ru_field, None)
            val_en = getattr(self, en_field, None)
            original = getattr(self, base_field, None)

            # 1) Если пользователь изменил base_field → определяем язык
            logger.info(
                f"auto_translate_fields вызвал для {base_field} | "
                f"{original}, {getattr(self, f'__{base_field}_old', None)}"
            )
            if original and (
                original != getattr(self, f"__{base_field}_old", None)
            ):

                source_lang = self.detect_lang(original)
                target_lang = "en" if source_lang == "ru" else "ru"

                # копируем в source_field
                if source_lang == "ru":
                    setattr(self, ru_field, original)
                elif source_lang == "en":
                    setattr(self, en_field, original)

                # Переводим в target_field
                translated = TranslationService.get_translation(
                    original,
                    source_lang,
                    target_lang,
                    context=f"{self.__class__.__name__}.{base_field}",
                )
                logger.info(
                    f"auto_translate_fields вызвал для {base_field} "
                    f"| {original} -> {translated}"
                )
                if translated:
                    if target_lang == "ru":
                        if val_ru != translated:
                            logger.info(
                                f"auto_translate_fields вызвал для "
                                f"{base_field} | setattr(self,"
                                f" {ru_field}, {translated})"
                            )
                            setattr(self, ru_field, translated)
                    elif target_lang == "en":
                        if val_en != translated:
                            logger.info(
                                f"auto_translate_fields вызвал для "
                                f"{base_field} | setattr(self, "
                                f"{en_field}, {translated})"
                            )
                            setattr(self, en_field, translated)

                # обновляем старое значение
                setattr(self, f"__{base_field}_old", original)
