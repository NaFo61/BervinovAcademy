from django.contrib.auth import get_user_model

# from .translation import translate_text  # noqa

User = get_user_model()

#
# @shared_task
# def translate_user_bio_task(user_id, bio):
#     try:
#         user = User.objects.get(pk=user_id)
#     except User.DoesNotExist:
#         return
#
#     try:
#         lang = detect(bio)
#     except LangDetectException:
#         lang = "unknown"
#
#     if lang == "ru":
#         user.bio_ru = bio
#         user.bio_en = translate_text(bio, src="ru", dest="en")
#     elif lang == "en":
#         user.bio_en = bio
#         user.bio_ru = translate_text(bio, src="en", dest="ru")
#     else:
#         # fallback: считаем русский по умолчанию
#         user.bio_ru = bio
#         user.bio_en = translate_text(bio, src="ru", dest="en")
#
#     user.save(update_fields=["bio_ru", "bio_en"])
