# from .tasks import translate_user_bio_task

# logger = logging.getLogger(__name__)
#
#
# @receiver(post_save, sender=User)
# def auto_translate_bio(sender, instance, created, **kwargs):
#     """
#     Автоматический перевод bio при каждом сохранении пользователя.
#     Работает только если bio не пустое.
#     Определяет язык текста и запускает Celery-таску для перевода.
#     """
#     bio_text = instance.bio
#     if not bio_text:
#         return
#
#     try:
#         detected_lang = detect(bio_text)
#     except LangDetectException:
#         logger.warning(
#             f"Не удалось определить язык для "
#             f"bio пользователя {instance.id}"
#         )
#         return
#
#     # если bio на русском → перевести на английский
#     if detected_lang == "ru":
#         # только если перевода еще нет или текст обновлен
#         if not instance.bio_en or instance.bio_en.strip() == "":
#             translate_user_bio_task.delay(instance.id, "ru", "en", bio_text)
#             logger.info(
#                 f"Создана таска перевода "
#                 f"bio для пользователя {instance.id}: ru → en"
#             )
#
#     # если bio на английском → перевести на русский
#     elif detected_lang == "en":
#         if not instance.bio_ru or instance.bio_ru.strip() == "":
#             translate_user_bio_task.delay(instance.id, "en", "ru", bio_text)
#             logger.info(
#                 f"Создана таска перевода "
#                 f"bio для пользователя {instance.id}: en → ru"
#             )
#
#     else:
#         logger.info(
#             f"Bio пользователя {instance.id} "
#             f"имеет неподдерживаемый язык: {detected_lang}"
#         )
