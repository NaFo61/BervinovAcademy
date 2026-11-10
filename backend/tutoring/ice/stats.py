"""Статистика репетитора из ICE — та же логика, что FinanceScreen в боте."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from datetime import timezone as dt_timezone
from zoneinfo import ZoneInfo

from django.utils import timezone

from tutoring.ice.db import ice_cursor
from tutoring.services import TutoringError

CHARGE_KINDS = ("lesson_charge", "refund")


def _week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def _month_start(day: date) -> date:
    return day.replace(day=1)


def _bucket_starts(date_from: date, date_to: date, group: str) -> list[date]:
    starts: list[date] = []
    if group == "week":
        cursor = _week_start(date_from)
        while cursor <= date_to:
            starts.append(cursor)
            cursor += timedelta(weeks=1)
    else:
        cursor = _month_start(date_from)
        while cursor <= date_to:
            starts.append(cursor)
            year, month = cursor.year, cursor.month + 1
            if month > 12:
                year, month = year + 1, 1
            cursor = date(year, month, 1)
    return starts


def _parse_period(
    *,
    date_from: str,
    date_to: str,
    group: str,
    month: str,
    tz: ZoneInfo,
) -> tuple[date, date, str]:
    group = (group or "week").strip().lower()
    if group not in ("week", "month"):
        raise TutoringError("group должен быть week или month.")

    if (date_from or "").strip() and (date_to or "").strip():
        try:
            start = date.fromisoformat(date_from.strip())
            end = date.fromisoformat(date_to.strip())
        except ValueError as exc:
            raise TutoringError("Даты в формате ГГГГ-ММ-ДД.") from exc
    else:
        text = (month or "").strip()
        local_now = timezone.now().astimezone(tz)
        if not text:
            start = date(local_now.year, local_now.month, 1)
            if local_now.month == 12:
                end = date(local_now.year, 12, 31)
            else:
                end = date(local_now.year, local_now.month + 1, 1) - timedelta(
                    days=1
                )
        else:
            try:
                year_text, mon_text = text.split("-", 1)
                year, mon = int(year_text), int(mon_text)
                if mon < 1 or mon > 12:
                    raise ValueError
            except ValueError as exc:
                raise TutoringError("Месяц в формате ГГГГ-ММ.") from exc
            start = date(year, mon, 1)
            if mon == 12:
                end = date(year, 12, 31)
            else:
                end = date(year, mon + 1, 1) - timedelta(days=1)
        group = "week"

    if start > end or (end - start).days > 366:
        raise TutoringError("Выберите период не больше года.")
    return start, end, group


def _tutor_tz(tutor_id: int) -> ZoneInfo:
    with ice_cursor() as cur:
        cur.execute("SELECT timezone FROM tutors WHERE id = %s", (tutor_id,))
        row = cur.fetchone()
    if row is None:
        raise TutoringError("Репетитор в боте не найден.", 404)
    name = (row.get("timezone") or "Europe/Moscow").strip()
    try:
        return ZoneInfo(name)
    except Exception:  # noqa: BLE001
        return ZoneInfo("Europe/Moscow")


def ice_period_stats(
    *,
    tutor_id: int,
    date_from: str = "",
    date_to: str = "",
    group: str = "week",
    month: str = "",
) -> dict:
    tz = _tutor_tz(tutor_id)
    start, end, group = _parse_period(
        date_from=date_from,
        date_to=date_to,
        group=group,
        month=month,
        tz=tz,
    )

    def local_day_to_utc(day: date) -> datetime:
        return datetime.combine(
            day, datetime.min.time(), tzinfo=tz
        ).astimezone(dt_timezone.utc)

    period_start = local_day_to_utc(start)
    period_end = local_day_to_utc(end + timedelta(days=1))
    now = timezone.now().astimezone(dt_timezone.utc)
    forecast_from = max(period_start, now)

    with ice_cursor() as cur:
        cur.execute(
            """
            SELECT COALESCE(SUM(-le.amount_kop), 0) AS total
            FROM ledger_entries le
            JOIN students s ON s.id = le.student_id
            WHERE s.tutor_id = %s
              AND le.kind::text = ANY(%s)
              AND le.occurred_at >= %s AND le.occurred_at < %s
            """,
            (tutor_id, list(CHARGE_KINDS), period_start, period_end),
        )
        charged_kop = int(cur.fetchone()["total"] or 0)

        cur.execute(
            """
            SELECT COALESCE(SUM(le.amount_kop), 0) AS total
            FROM ledger_entries le
            JOIN students s ON s.id = le.student_id
            WHERE s.tutor_id = %s
              AND le.kind::text = 'payment'
              AND le.occurred_at >= %s AND le.occurred_at < %s
            """,
            (tutor_id, period_start, period_end),
        )
        received_kop = int(cur.fetchone()["total"] or 0)

        cur.execute(
            """
            SELECT COALESCE(SUM(price_kop), 0) AS total
            FROM lessons
            WHERE tutor_id = %s
              AND status::text = 'confirmed'
              AND starts_at >= %s AND starts_at < %s
            """,
            (tutor_id, forecast_from, period_end),
        )
        forecast_kop = int(cur.fetchone()["total"] or 0)

        def count_status(status: str) -> int:
            sql = """
                SELECT COUNT(*) AS total FROM lessons
                WHERE tutor_id = %s
                  AND status::text = %s
                  AND starts_at >= %s AND starts_at < %s
            """
            params: list = [tutor_id, status, period_start, period_end]
            if status == "cancelled":
                sql += """
                  AND id NOT IN (
                    SELECT rescheduled_from_id FROM lessons
                    WHERE tutor_id = %s AND rescheduled_from_id IS NOT NULL
                  )
                """
                params.append(tutor_id)
            cur.execute(sql, params)
            return int(cur.fetchone()["total"] or 0)

        completed_count = count_status("completed")
        cancelled_count = count_status("cancelled")
        no_show_count = count_status("no_show")

        # Buckets: date_trunc in tutor TZ.
        cur.execute(
            """
            SELECT date_trunc(%s, timezone(%s, le.occurred_at))::date AS bucket,
                   COALESCE(SUM(CASE WHEN le.kind::text = ANY(%s)
                                     THEN -le.amount_kop ELSE 0 END), 0)
                     AS charged,
                   COALESCE(SUM(CASE WHEN le.kind::text = 'payment'
                                     THEN le.amount_kop ELSE 0 END), 0)
                     AS received
            FROM ledger_entries le
            JOIN students s ON s.id = le.student_id
            WHERE s.tutor_id = %s
              AND le.occurred_at >= %s AND le.occurred_at < %s
            GROUP BY 1
            """,
            (
                group,
                str(tz),
                list(CHARGE_KINDS),
                tutor_id,
                period_start,
                period_end,
            ),
        )
        money_by_bucket = {
            row["bucket"]: (
                int(row["charged"] or 0),
                int(row["received"] or 0),
            )
            for row in cur.fetchall()
        }

        cur.execute(
            """
            SELECT date_trunc(%s, timezone(%s, starts_at))::date AS bucket,
                   COALESCE(SUM(price_kop), 0) AS total
            FROM lessons
            WHERE tutor_id = %s
              AND status::text = 'confirmed'
              AND starts_at >= %s AND starts_at < %s
            GROUP BY 1
            """,
            (group, str(tz), tutor_id, forecast_from, period_end),
        )
        forecast_by_bucket = {
            row["bucket"]: int(row["total"] or 0) for row in cur.fetchall()
        }

        cur.execute(
            """
            SELECT s.id AS student_id, s.display_name,
                   COALESCE(SUM(le.amount_kop), 0) AS balance_kop
            FROM students s
            LEFT JOIN ledger_entries le ON le.student_id = s.id
            WHERE s.tutor_id = %s
            GROUP BY s.id, s.display_name
            HAVING COALESCE(SUM(le.amount_kop), 0) < 0
            ORDER BY balance_kop ASC
            """,
            (tutor_id,),
        )
        debtors = [
            {
                "student_id": row["student_id"],
                "display_name": row["display_name"],
                "balance_kop": int(row["balance_kop"] or 0),
                "student": {
                    "public_id": str(row["student_id"]),
                    "name": row["display_name"],
                },
            }
            for row in cur.fetchall()
        ]

        cur.execute(
            """
            SELECT s.id AS student_id, s.display_name,
                   COALESCE(SUM(CASE WHEN le.kind::text = ANY(%s)
                                     THEN -le.amount_kop ELSE 0 END), 0)
                     AS charged_kop,
                   COALESCE(SUM(CASE WHEN le.kind::text = 'payment'
                                     THEN le.amount_kop ELSE 0 END), 0)
                     AS received_kop
            FROM students s
            LEFT JOIN ledger_entries le
              ON le.student_id = s.id
             AND le.occurred_at >= %s AND le.occurred_at < %s
            WHERE s.tutor_id = %s
            GROUP BY s.id, s.display_name
            HAVING COALESCE(SUM(CASE WHEN le.kind::text = ANY(%s)
                                     THEN -le.amount_kop ELSE 0 END), 0) <> 0
                OR COALESCE(SUM(CASE WHEN le.kind::text = 'payment'
                                     THEN le.amount_kop ELSE 0 END), 0) <> 0
            ORDER BY charged_kop DESC
            """,
            (
                list(CHARGE_KINDS),
                period_start,
                period_end,
                tutor_id,
                list(CHARGE_KINDS),
            ),
        )
        by_student = [
            {
                "student_id": row["student_id"],
                "display_name": row["display_name"],
                "charged_kop": int(row["charged_kop"] or 0),
                "received_kop": int(row["received_kop"] or 0),
            }
            for row in cur.fetchall()
        ]

    buckets = []
    for bucket_start in _bucket_starts(start, end, group):
        charged, received = money_by_bucket.get(bucket_start, (0, 0))
        buckets.append(
            {
                "period_start": bucket_start.isoformat(),
                "charged_kop": charged,
                "received_kop": received,
                "forecast_kop": forecast_by_bucket.get(bucket_start, 0),
            }
        )

    return {
        "source": "ice",
        "from": start.isoformat(),
        "to": end.isoformat(),
        "group": group,
        "month": f"{start.year:04d}-{start.month:02d}",
        "charged_kop": charged_kop,
        "received_kop": received_kop,
        "forecast_kop": forecast_kop,
        "completed_count": completed_count,
        "cancelled_count": cancelled_count,
        "no_show_count": no_show_count,
        "buckets": buckets,
        "by_student": by_student,
        "debtors": debtors,
    }
