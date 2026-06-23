from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from content.editor_registry import (
    LESSON_KINDS,
    build_course_editor_outline,
    course_for_lesson,
    create_lesson_in_module,
    get_lesson,
    user_can_edit_course,
)
from content.editor_serializers import EDITOR_SERIALIZERS
from content.models import Course, Module
from mentoring.permissions import IsMentorOrAdmin


def _editor_context(request):
    return {"request": request}


def _check_course_access(request, course: Course):
    if not user_can_edit_course(request.user, course):
        return Response(
            {"detail": "Нет доступа к редактированию курса."}, status=403
        )
    return None


def _check_lesson_access(request, instance):
    course = course_for_lesson(instance)
    if not course:
        return Response({"detail": "Урок не привязан к курсу."}, status=400)
    return _check_course_access(request, course)


class CourseEditorOutlineView(APIView):
    """``GET /api/mentoring/editor/courses/{course_public_id}/`` — структура курса."""

    permission_classes = [IsAuthenticated, IsMentorOrAdmin]

    def get(self, request, course_public_id):
        course = get_object_or_404(Course, public_id=course_public_id)
        denied = _check_course_access(request, course)
        if denied:
            return denied
        return Response(build_course_editor_outline(course))


class LessonEditorView(APIView):
    """
    ``GET/PATCH/DELETE /api/mentoring/editor/lessons/{kind}/{public_id}/``

    PATCH поддерживает multipart для ``video_file``.
    """

    permission_classes = [IsAuthenticated, IsMentorOrAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request, kind, public_id):
        if kind not in LESSON_KINDS:
            return Response({"detail": "Неизвестный тип урока."}, status=400)
        instance = get_lesson(kind, public_id)
        denied = _check_lesson_access(request, instance)
        if denied:
            return denied
        ser_cls = EDITOR_SERIALIZERS[kind]
        if kind in ("radio", "checkbox"):
            instance = (
                type(instance)
                .objects.prefetch_related("answers")
                .get(pk=instance.pk)
            )
        elif kind == "coding":
            instance = (
                type(instance)
                .objects.prefetch_related("test_cases")
                .get(pk=instance.pk)
            )
        return Response(
            ser_cls(instance, context=_editor_context(request)).data
        )

    def patch(self, request, kind, public_id):
        if kind not in LESSON_KINDS:
            return Response({"detail": "Неизвестный тип урока."}, status=400)
        instance = get_lesson(kind, public_id)
        denied = _check_lesson_access(request, instance)
        if denied:
            return denied

        data = request.data.copy()
        if "answer_options" in data and isinstance(
            data["answer_options"], str
        ):
            import json

            try:
                data["answer_options"] = json.loads(data["answer_options"])
            except json.JSONDecodeError:
                return Response(
                    {"answer_options": "Некорректный JSON."}, status=400
                )
        if "test_cases" in data and isinstance(data["test_cases"], str):
            import json

            try:
                data["test_cases"] = json.loads(data["test_cases"])
            except json.JSONDecodeError:
                return Response(
                    {"test_cases": "Некорректный JSON."}, status=400
                )

        ser_cls = EDITOR_SERIALIZERS[kind]
        if kind in ("radio", "checkbox"):
            instance = (
                type(instance)
                .objects.prefetch_related("answers")
                .get(pk=instance.pk)
            )
        elif kind == "coding":
            instance = (
                type(instance)
                .objects.prefetch_related("test_cases")
                .get(pk=instance.pk)
            )

        serializer = ser_cls(
            instance,
            data=data,
            partial=True,
            context=_editor_context(request),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, kind, public_id):
        if kind not in LESSON_KINDS:
            return Response({"detail": "Неизвестный тип урока."}, status=400)
        instance = get_lesson(kind, public_id)
        denied = _check_lesson_access(request, instance)
        if denied:
            return denied
        instance.is_active = False
        instance.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class LessonEditorCreateView(APIView):
    """``POST /api/mentoring/editor/modules/{module_public_id}/lessons/``"""

    permission_classes = [IsAuthenticated, IsMentorOrAdmin]

    def post(self, request, module_public_id):
        module = get_object_or_404(
            Module.objects.select_related("course"),
            public_id=module_public_id,
        )
        denied = _check_course_access(request, module.course)
        if denied:
            return denied

        kind = (request.data.get("kind") or "").strip()
        title = (request.data.get("title") or "").strip() or "Новый урок"
        if kind not in LESSON_KINDS:
            return Response(
                {"kind": "Укажите theory, radio, checkbox или coding."},
                status=400,
            )

        instance = create_lesson_in_module(module, kind, title=title)
        if kind in ("radio", "checkbox"):
            instance = (
                type(instance)
                .objects.prefetch_related("answers")
                .get(pk=instance.pk)
            )
        elif kind == "coding":
            instance = (
                type(instance)
                .objects.prefetch_related("test_cases")
                .get(pk=instance.pk)
            )
        ser_cls = EDITOR_SERIALIZERS[kind]
        return Response(
            ser_cls(instance, context=_editor_context(request)).data,
            status=status.HTTP_201_CREATED,
        )
