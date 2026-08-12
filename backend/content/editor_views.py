from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from unidecode import unidecode

from content.editor_registry import (
    LESSON_KINDS,
    build_course_editor_outline,
    course_for_lesson,
    create_lesson_in_module,
    get_lesson,
    user_can_edit_course,
)
from content.editor_serializers import EDITOR_SERIALIZERS
from content.models import Course, Exam, Module, Technology
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


def _unique_slug(title: str) -> str:
    base = slugify(unidecode(title)) or "course"
    slug = base
    n = 1
    while Course.objects.filter(slug=slug).exists():
        n += 1
        slug = f"{base}-{n}"
    return slug


class CourseEditorCreateView(APIView):
    """``POST /api/mentoring/editor/courses/`` — создать курс (ментор = автор)."""

    permission_classes = [IsAuthenticated, IsMentorOrAdmin]

    def post(self, request):
        title = (request.data.get("title") or "").strip()
        if not title:
            return Response({"title": "Укажите название."}, status=400)
        description = (request.data.get("description") or "").strip()
        course = Course.objects.create(
            title=title,
            description=description or title,
            slug=_unique_slug(title),
            is_active=True,
            mentor=request.user,
        )
        tech_ids = request.data.get("technology_public_ids") or []
        if isinstance(tech_ids, list) and tech_ids:
            techs = Technology.objects.filter(public_id__in=tech_ids)
            course.technology.set(techs)
        return Response(
            build_course_editor_outline(course),
            status=status.HTTP_201_CREATED,
        )


class CourseEditorOutlineView(APIView):
    """``GET/PATCH /api/mentoring/editor/courses/{course_public_id}/``."""

    permission_classes = [IsAuthenticated, IsMentorOrAdmin]

    def get(self, request, course_public_id):
        course = get_object_or_404(Course, public_id=course_public_id)
        denied = _check_course_access(request, course)
        if denied:
            return denied
        return Response(build_course_editor_outline(course))

    def patch(self, request, course_public_id):
        course = get_object_or_404(Course, public_id=course_public_id)
        denied = _check_course_access(request, course)
        if denied:
            return denied
        if "title" in request.data:
            title = (request.data.get("title") or "").strip()
            if title:
                course.title = title
        if "description" in request.data:
            course.description = request.data.get("description") or ""
        if "assistant_prompt" in request.data:
            course.assistant_prompt = (
                request.data.get("assistant_prompt") or ""
            )
        if "is_active" in request.data:
            course.is_active = bool(request.data.get("is_active"))
        course.save()
        return Response(build_course_editor_outline(course))


class ModuleEditorCreateView(APIView):
    """``POST /api/mentoring/editor/courses/{course_public_id}/modules/``"""

    permission_classes = [IsAuthenticated, IsMentorOrAdmin]

    def post(self, request, course_public_id):
        course = get_object_or_404(Course, public_id=course_public_id)
        denied = _check_course_access(request, course)
        if denied:
            return denied
        title = (request.data.get("title") or "").strip() or "Новый модуль"
        description = (request.data.get("description") or "").strip()
        module = Module.objects.create(
            course=course,
            title=title,
            description=description,
            is_active=True,
        )
        return Response(
            {
                "public_id": str(module.public_id),
                "title": module.title,
                "description": module.description,
                "assistant_prompt": module.assistant_prompt or "",
                "order_index": module.order_index,
                "is_active": module.is_active,
                "lessons": [],
            },
            status=status.HTTP_201_CREATED,
        )


class ModuleEditorDetailView(APIView):
    """``PATCH/DELETE /api/mentoring/editor/modules/{module_public_id}/``"""

    permission_classes = [IsAuthenticated, IsMentorOrAdmin]

    def patch(self, request, module_public_id):
        module = get_object_or_404(
            Module.objects.select_related("course"),
            public_id=module_public_id,
        )
        denied = _check_course_access(request, module.course)
        if denied:
            return denied
        if "title" in request.data:
            title = (request.data.get("title") or "").strip()
            if title:
                module.title = title
        if "description" in request.data:
            module.description = request.data.get("description") or ""
        if "assistant_prompt" in request.data:
            module.assistant_prompt = (
                request.data.get("assistant_prompt") or ""
            )
        if "is_active" in request.data:
            module.is_active = bool(request.data.get("is_active"))
        module.save()
        return Response(
            {
                "public_id": str(module.public_id),
                "title": module.title,
                "description": module.description,
                "assistant_prompt": module.assistant_prompt or "",
                "order_index": module.order_index,
                "is_active": module.is_active,
            }
        )

    def delete(self, request, module_public_id):
        module = get_object_or_404(
            Module.objects.select_related("course"),
            public_id=module_public_id,
        )
        denied = _check_course_access(request, module.course)
        if denied:
            return denied
        module.is_active = False
        module.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class ExamEditorCreateView(APIView):
    """``POST /api/mentoring/editor/courses/{course_public_id}/exams/``"""

    permission_classes = [IsAuthenticated, IsMentorOrAdmin]

    def post(self, request, course_public_id):
        course = get_object_or_404(Course, public_id=course_public_id)
        denied = _check_course_access(request, course)
        if denied:
            return denied
        title = (request.data.get("title") or "").strip() or "Контрольная"
        duration = request.data.get("duration_minutes", 45)
        try:
            duration = max(1, int(duration))
        except (TypeError, ValueError):
            duration = 45
        exam = Exam.objects.create(
            course=course,
            title=title,
            description=(request.data.get("description") or "").strip(),
            duration_minutes=duration,
            is_active=True,
            mentor_unlock_required=bool(
                request.data.get("mentor_unlock_required", False)
            ),
        )
        return Response(
            {
                "public_id": str(exam.public_id),
                "title": exam.title,
                "order_index": exam.order_index,
                "duration_minutes": exam.duration_minutes,
            },
            status=status.HTTP_201_CREATED,
        )


class TechnologyListEditorView(APIView):
    """``GET /api/mentoring/editor/technologies/`` — справочник для создания курса."""

    permission_classes = [IsAuthenticated, IsMentorOrAdmin]

    def get(self, request):
        rows = [
            {"public_id": str(t.public_id), "name": t.name}
            for t in Technology.objects.order_by("name")
        ]
        return Response(rows)


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
                {
                    "kind": "Укажите theory, radio, checkbox, short_answer или coding."
                },
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
