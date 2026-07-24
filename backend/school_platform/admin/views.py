from datetime import timedelta
import json

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone
from django.utils.translation import gettext as _

User = get_user_model()


def dashboard_callback(request, context):
    now = timezone.now()
    month_ago = now - timedelta(days=30)

    total_users = User.objects.count()
    total_courses = 0
    active_students = 0
    completed_courses = 0
    course_names = []
    course_counts = []

    try:
        from content.models import Course
        from education.models import Enrollment

        total_courses = Course.objects.count()
        active_students = (
            Enrollment.objects.filter(status=Enrollment.Status.ACTIVE)
            .values("user_id")
            .distinct()
            .count()
        )
        completed_courses = Enrollment.objects.filter(
            status=Enrollment.Status.COMPLETED
        ).count()

        top = (
            Enrollment.objects.values("course__title")
            .annotate(c=Count("id"))
            .order_by("-c")[:7]
        )
        course_names = [row["course__title"] or "—" for row in top]
        course_counts = [row["c"] for row in top]
    except Exception:
        pass

    months = []
    activity_data = []
    for i in range(5, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=32 * i)).replace(
            day=1
        )
        months.append(month_start.strftime("%b"))
        next_month = (month_start + timedelta(days=32)).replace(day=1)
        activity_data.append(
            User.objects.filter(
                date_joined__gte=month_start, date_joined__lt=next_month
            ).count()
        )

    if not course_names:
        course_names = [_("Нет данных")]
        course_counts = [0]

    context.update(
        {
            "total_users": total_users,
            "total_courses": total_courses,
            "active_students": active_students,
            "completed_courses": completed_courses,
            "months_json": json.dumps(months, ensure_ascii=False),
            "activity_data_json": json.dumps(activity_data),
            "course_names_json": json.dumps(course_names, ensure_ascii=False),
            "course_counts_json": json.dumps(course_counts),
            "users_last_30_days": User.objects.filter(
                date_joined__gte=month_ago
            ).count(),
        }
    )
    return context
