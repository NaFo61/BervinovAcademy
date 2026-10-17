from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from mentoring.permissions import IsAdminRole, IsMentorOrAdmin
from tutoring.services import (
    TutoringError,
    availability_payload,
    book_lesson,
    cancel_lesson,
    claim_payload,
    confirm_claim,
    create_claim,
    find_student,
    grant_access,
    lesson_payload,
    mark_lesson,
    me_payload,
    month_stats,
    move_lesson,
    pending_and_debtors,
    reject_claim,
    replace_availability,
    replace_tariffs,
    resolve_mentor_actor,
    tariffs_payload,
    visible_lessons,
)
from tutoring.slots import SlotError, parse_day, slots_for_day
from tutoring.telegram_auth import TelegramInitDataAuthentication


def _guard(exc: TutoringError) -> Response:
    return Response({"detail": exc.detail}, status=exc.status_code)


class TutoringView(APIView):
    authentication_classes = [
        JWTAuthentication,
        TelegramInitDataAuthentication,
    ]
    permission_classes = [IsAuthenticated]


class MeView(TutoringView):
    def get(self, request):
        return Response(me_payload(request.user))


class SlotListView(TutoringView):
    def get(self, request):
        from tutoring.access import assigned_mentor, can_book

        if not can_book(request.user):
            return Response(
                {"detail": "Запись на занятия закрыта."}, status=403
            )
        mentor = assigned_mentor(request.user)
        try:
            day = parse_day(request.query_params.get("date") or "")
            duration = int(request.query_params.get("duration") or "")
            found = slots_for_day(
                mentor=mentor, day=day, duration_minutes=duration
            )
        except (SlotError, ValueError) as exc:
            detail = getattr(exc, "detail", "Нужны дата и длительность.")
            return Response({"detail": detail}, status=400)
        return Response({"slots": [item.isoformat() for item in found]})


class LessonListView(TutoringView):
    def get(self, request):
        lessons = visible_lessons(request.user)[:300]
        return Response(
            {"results": [lesson_payload(item) for item in lessons]}
        )

    def post(self, request):
        if request.user.role != "student":
            return Response({"detail": "Записывается ученик."}, status=403)
        try:
            lesson = book_lesson(
                student=request.user,
                starts_at=request.data.get("starts_at"),
                duration_minutes=request.data.get("duration_minutes"),
            )
        except TutoringError as exc:
            return _guard(exc)
        return Response(lesson_payload(lesson), status=201)


class LessonActionView(TutoringView):
    def post(self, request, public_id, action):
        try:
            if action == "cancel":
                lesson = cancel_lesson(actor=request.user, public_id=public_id)
            elif action == "move":
                lesson = move_lesson(
                    actor=request.user,
                    public_id=public_id,
                    starts_at=request.data.get("starts_at"),
                )
            elif action == "done":
                lesson = mark_lesson(
                    actor=request.user, public_id=public_id, status="done"
                )
            elif action == "missed":
                lesson = mark_lesson(
                    actor=request.user, public_id=public_id, status="missed"
                )
            else:
                return Response(
                    {"detail": "Неизвестное действие."}, status=404
                )
        except TutoringError as exc:
            return _guard(exc)
        return Response(lesson_payload(lesson))


class PaymentClaimListView(TutoringView):
    def get(self, request):
        return Response(pending_and_debtors(request.user))

    def post(self, request):
        if request.user.role != "student":
            return Response({"detail": "Оплату отмечает ученик."}, status=403)
        try:
            claim = create_claim(
                student=request.user,
                amount_kop=request.data.get("amount_kop"),
            )
        except TutoringError as exc:
            return _guard(exc)
        return Response(claim_payload(claim), status=201)


class PaymentClaimActionView(TutoringView):
    def post(self, request, public_id, action):
        if request.user.role not in ("mentor", "admin"):
            return Response({"detail": "Решает ментор."}, status=403)
        try:
            if action == "confirm":
                claim = confirm_claim(actor=request.user, public_id=public_id)
            elif action == "reject":
                claim = reject_claim(actor=request.user, public_id=public_id)
            else:
                return Response(
                    {"detail": "Неизвестное действие."}, status=404
                )
        except TutoringError as exc:
            return _guard(exc)
        return Response(claim_payload(claim))


class MentorAvailabilityView(TutoringView):
    permission_classes = [IsAuthenticated, IsMentorOrAdmin]

    def get(self, request):
        try:
            mentor = resolve_mentor_actor(
                request.user, request.query_params.get("mentor")
            )
        except TutoringError as exc:
            return _guard(exc)
        return Response(availability_payload(mentor))

    def put(self, request):
        try:
            mentor = resolve_mentor_actor(
                request.user, request.data.get("mentor_public_id")
            )
            payload = replace_availability(
                mentor=mentor,
                timezone_name=request.data.get("timezone") or "Europe/Moscow",
                windows=request.data.get("windows") or [],
            )
        except TutoringError as exc:
            return _guard(exc)
        return Response(payload)


class MentorTariffsView(TutoringView):
    permission_classes = [IsAuthenticated, IsMentorOrAdmin]

    def get(self, request):
        try:
            mentor = resolve_mentor_actor(
                request.user, request.query_params.get("mentor")
            )
        except TutoringError as exc:
            return _guard(exc)
        return Response({"tariffs": tariffs_payload(mentor)})

    def put(self, request):
        try:
            mentor = resolve_mentor_actor(
                request.user, request.data.get("mentor_public_id")
            )
            tariffs = replace_tariffs(
                mentor=mentor, tariffs=request.data.get("tariffs") or []
            )
        except TutoringError as exc:
            return _guard(exc)
        return Response({"tariffs": tariffs})


class MentorStatsView(TutoringView):
    permission_classes = [IsAuthenticated, IsMentorOrAdmin]

    def get(self, request):
        try:
            mentor = resolve_mentor_actor(
                request.user, request.query_params.get("mentor")
            )
            payload = month_stats(
                mentor=mentor, month=request.query_params.get("month") or ""
            )
        except TutoringError as exc:
            return _guard(exc)
        return Response(payload)


class LessonAccessView(TutoringView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        try:
            student = find_student(
                email=request.data.get("email") or "",
                public_id=str(request.data.get("user_public_id") or ""),
            )
            mentor = None
            raw_mentor = request.data.get("mentor_public_id")
            if raw_mentor:
                from django.contrib.auth import get_user_model

                mentor = (
                    get_user_model()
                    .objects.filter(public_id=raw_mentor)
                    .first()
                )
                if mentor is None:
                    raise TutoringError("Ментор не найден.", 404)
            payload = grant_access(
                actor=request.user,
                student=student,
                enabled=bool(request.data.get("enabled", True)),
                mentor=mentor,
            )
        except TutoringError as exc:
            return _guard(exc)
        return Response(payload)
