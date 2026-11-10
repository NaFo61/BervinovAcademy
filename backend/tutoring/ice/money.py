"""Оплаты и долги из ICE (та же касса, что в боте)."""

from __future__ import annotations

from datetime import datetime
from datetime import timezone as dt_timezone
from uuid import uuid4

from tutoring.ice.db import ice_cursor
from tutoring.services import TutoringError


def ice_pending_and_debtors(*, tutor_id: int) -> dict:
    with ice_cursor() as cur:
        cur.execute(
            """
            SELECT pc.id, pc.amount_kop, pc.status::text AS status,
                   pc.created_at, s.id AS student_id, s.display_name
            FROM payment_claims pc
            JOIN students s ON s.id = pc.student_id
            WHERE s.tutor_id = %s AND pc.status::text = 'pending'
            ORDER BY pc.created_at DESC
            """,
            (tutor_id,),
        )
        pending = [
            {
                "public_id": str(row["id"]),
                "amount_kop": int(row["amount_kop"]),
                "status": row["status"],
                "created_at": (
                    row["created_at"].isoformat()
                    if row["created_at"]
                    else None
                ),
                "student": {
                    "public_id": str(row["student_id"]),
                    "name": row["display_name"],
                },
                "source": "ice",
            }
            for row in cur.fetchall()
        ]

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
                "student": {
                    "public_id": str(row["student_id"]),
                    "name": row["display_name"],
                },
                "balance_kop": int(row["balance_kop"] or 0),
                "source": "ice",
            }
            for row in cur.fetchall()
        ]

    return {"pending": pending, "debtors": debtors, "source": "ice"}


def ice_decide_claim(*, tutor_id: int, claim_id: int, action: str) -> dict:
    if action not in ("confirm", "reject"):
        raise TutoringError("Неизвестное действие.", 404)
    now = datetime.now(dt_timezone.utc)
    with ice_cursor() as cur:
        cur.execute(
            """
            SELECT pc.id, pc.student_id, pc.amount_kop, pc.status::text AS status,
                   s.display_name
            FROM payment_claims pc
            JOIN students s ON s.id = pc.student_id
            WHERE pc.id = %s AND s.tutor_id = %s
            FOR UPDATE OF pc
            """,
            (claim_id, tutor_id),
        )
        row = cur.fetchone()
        if row is None:
            raise TutoringError("Заявка не найдена.", 404)
        if row["status"] != "pending":
            raise TutoringError("Заявка уже решена.", 409)

        if action == "confirm":
            cur.execute(
                """
                UPDATE payment_claims
                SET status = 'confirmed'::payment_claim_status, decided_at = %s
                WHERE id = %s
                """,
                (now, claim_id),
            )
            cur.execute(
                """
                INSERT INTO ledger_entries
                  (student_id, kind, amount_kop, method, note,
                   occurred_at, created_at, operation_id)
                VALUES
                  (%s, 'payment'::ledger_kind, %s, 'transfer'::ledger_method,
                   %s, %s, %s, %s)
                """,
                (
                    row["student_id"],
                    int(row["amount_kop"]),
                    f"claim:{claim_id}",
                    now,
                    now,
                    str(uuid4()),
                ),
            )
            status = "confirmed"
        else:
            cur.execute(
                """
                UPDATE payment_claims
                SET status = 'rejected'::payment_claim_status, decided_at = %s
                WHERE id = %s
                """,
                (now, claim_id),
            )
            status = "rejected"

    return {
        "public_id": str(claim_id),
        "amount_kop": int(row["amount_kop"]),
        "status": status,
        "student": {
            "public_id": str(row["student_id"]),
            "name": row["display_name"],
        },
        "source": "ice",
    }
