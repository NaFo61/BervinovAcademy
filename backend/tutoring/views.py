from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from mentoring.permissions import IsAdminRole, IsMentorOrAdmin
from tutoring.ice.db import ice_configured
from tutoring.ice.link import (
    ice_status,
    link_user_to_ice,
    resolve_ice_tutor_id,
)
from tutoring.ice.money import ice_decide_claim, ice_pending_and_debtors
from tutoring.ice.stats import ice_period_stats
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
    save_lesson_journal,
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
            elif action == "notes":
                lesson = save_lesson_journal(
                    actor=request.user,
                    public_id=public_id,
                    homework_status=request.data.get("homework_status", ""),
                    learned_note=request.data.get("learned_note", ""),
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
        if ice_configured() and request.user.role in ("mentor", "admin"):
            try:
                tutor_id = resolve_ice_tutor_id(
                    request.user, request.query_params.get("mentor")
                )
                return Response(ice_pending_and_debtors(tutor_id=tutor_id))
            except TutoringError:
                # Нет привязки — локальная касса академии.
                pass
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
            claim_id = None
            try:
                claim_id = int(str(public_id))
            except (TypeError, ValueError):
                claim_id = None
            if ice_configured() and claim_id is not None:
                from tutoring.models import TutoringIceLink

                if TutoringIceLink.objects.filter(user=request.user).exists():
                    tutor_id = resolve_ice_tutor_id(
                        request.user, request.data.get("mentor")
                    )
                    return Response(
                        ice_decide_claim(
                            tutor_id=tutor_id,
                            claim_id=claim_id,
                            action=action,
                        )
                    )
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
            use_ice = False
            if ice_configured():
                try:
                    tutor_id = resolve_ice_tutor_id(
                        request.user, request.query_params.get("mentor")
                    )
                    use_ice = True
                except TutoringError as exc:
                    # Нет привязки — показываем локальную кассу, не 409.
                    if exc.status_code not in (404, 409):
                        return _guard(exc)
            if use_ice:
                payload = ice_period_stats(
                    tutor_id=tutor_id,
                    date_from=request.query_params.get("from") or "",
                    date_to=request.query_params.get("to") or "",
                    group=request.query_params.get("group") or "week",
                    month=request.query_params.get("month") or "",
                )
            else:
                mentor = resolve_mentor_actor(
                    request.user, request.query_params.get("mentor")
                )
                payload = month_stats(
                    mentor=mentor,
                    month=request.query_params.get("month") or "",
                )
                payload["source"] = "local"
                payload["buckets"] = []
                payload["by_student"] = []
                payload["debtors"] = []
                payload["completed_count"] = 0
                payload["cancelled_count"] = 0
                payload["no_show_count"] = 0
        except TutoringError as exc:
            return _guard(exc)
        return Response(payload)


class IceStatusView(TutoringView):
    permission_classes = [IsAuthenticated, IsMentorOrAdmin]

    def get(self, request):
        return Response(ice_status(request.user))


class IceLinkView(TutoringView):
    permission_classes = [IsAuthenticated, IsMentorOrAdmin]

    def post(self, request):
        try:
            raw = request.data.get("ice_tutor_id")
            ice_tutor_id = int(raw) if raw not in (None, "") else None
            link = link_user_to_ice(
                user=request.user, ice_tutor_id=ice_tutor_id
            )
        except (TypeError, ValueError):
            return Response(
                {"detail": "ice_tutor_id должен быть числом."}, status=400
            )
        except TutoringError as exc:
            return _guard(exc)
        return Response(
            {
                "ice_tutor_id": link.ice_tutor_id,
                "display_name": link.display_name,
                "telegram_id": link.telegram_id,
                "status": ice_status(request.user),
            }
        )


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
