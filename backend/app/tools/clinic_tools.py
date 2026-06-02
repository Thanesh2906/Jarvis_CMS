from datetime import date
from decimal import Decimal
from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.rbac import can_view_sensitive_patient_data


def _money(value: Any) -> float:
    if isinstance(value, Decimal):
        return float(value)
    return float(value or 0)


async def get_today_patient_count(db: AsyncSession, role: str) -> dict[str, Any]:
    result = await db.execute(text("SELECT COUNT(*) FROM patients WHERE DATE(created_at) = CURRENT_DATE"))
    return {"count": result.scalar_one()}


async def get_today_appointment_count(db: AsyncSession, role: str) -> dict[str, Any]:
    result = await db.execute(text("SELECT COUNT(*) FROM appointments WHERE appointment_date = CURRENT_DATE"))
    return {"count": result.scalar_one()}


async def get_pending_lab_results(db: AsyncSession, role: str) -> dict[str, Any]:
    result = await db.execute(text("SELECT COUNT(*) FROM lab_results WHERE status = 'pending'"))
    return {"count": result.scalar_one()}


async def get_unpaid_invoice_count(db: AsyncSession, role: str) -> dict[str, Any]:
    result = await db.execute(text("SELECT COUNT(*) FROM invoices WHERE status IN ('unpaid', 'overdue')"))
    return {"count": result.scalar_one()}


async def get_today_revenue(db: AsyncSession, role: str) -> dict[str, Any]:
    result = await db.execute(text("SELECT COALESCE(SUM(amount_paid), 0) FROM invoices WHERE DATE(paid_at) = CURRENT_DATE"))
    return {"revenue": _money(result.scalar_one()), "currency": "USD"}


async def search_patient_by_name(db: AsyncSession, role: str, name: str) -> list[dict[str, Any]]:
    pattern = f"%{name}%"
    result = await db.execute(
        text(
            """
            SELECT id, first_name, last_name, date_of_birth, phone, email, medical_record_number
            FROM patients
            WHERE CONCAT(first_name, ' ', last_name) LIKE :pattern
            ORDER BY last_name, first_name
            LIMIT 10
            """
        ),
        {"pattern": pattern},
    )
    rows = [dict(row._mapping) for row in result]
    if can_view_sensitive_patient_data(role):
        return rows
    return [
        {
            "id": row["id"],
            "first_name": row["first_name"],
            "last_name": row["last_name"],
            "medical_record_number": row["medical_record_number"],
        }
        for row in rows
    ]


async def get_patient_summary(db: AsyncSession, role: str, patient_id: int) -> dict[str, Any]:
    patient_result = await db.execute(
        text(
            """
            SELECT id, first_name, last_name, date_of_birth, phone, email, address, medical_record_number
            FROM patients WHERE id = :patient_id
            """
        ),
        {"patient_id": patient_id},
    )
    patient = patient_result.mappings().first()
    if patient is None:
        return {"error": "Patient not found"}

    appointment_result = await db.execute(
        text(
            """
            SELECT appointment_date, start_time, status, reason
            FROM appointments
            WHERE patient_id = :patient_id
            ORDER BY appointment_date DESC
            LIMIT 5
            """
        ),
        {"patient_id": patient_id},
    )
    lab_result = await db.execute(
        text(
            """
            SELECT lo.test_name, lr.status, lr.resulted_at
            FROM lab_orders lo
            LEFT JOIN lab_results lr ON lr.lab_order_id = lo.id
            WHERE lo.patient_id = :patient_id
            ORDER BY lo.ordered_at DESC
            LIMIT 5
            """
        ),
        {"patient_id": patient_id},
    )
    summary = {
        "patient": dict(patient),
        "recent_appointments": [dict(row._mapping) for row in appointment_result],
        "recent_labs": [dict(row._mapping) for row in lab_result],
    }
    if not can_view_sensitive_patient_data(role):
        summary["patient"].pop("date_of_birth", None)
        summary["patient"].pop("phone", None)
        summary["patient"].pop("email", None)
        summary["patient"].pop("address", None)
    return summary


async def get_doctor_schedule(db: AsyncSession, role: str, date: str) -> list[dict[str, Any]]:
    result = await db.execute(
        text(
            """
            SELECT d.full_name AS doctor_name, a.start_time, a.status,
                   p.id AS patient_id, p.first_name, p.last_name, a.reason
            FROM appointments a
            JOIN doctors d ON d.id = a.doctor_id
            JOIN patients p ON p.id = a.patient_id
            WHERE a.appointment_date = :date
            ORDER BY d.full_name, a.start_time
            """
        ),
        {"date": date},
    )
    rows = [dict(row._mapping) for row in result]
    if can_view_sensitive_patient_data(role):
        return rows
    return [{k: v for k, v in row.items() if k != "reason"} for row in rows]


async def get_lab_pending_by_date(db: AsyncSession, role: str, date: str) -> list[dict[str, Any]]:
    result = await db.execute(
        text(
            """
            SELECT lo.id AS lab_order_id, lo.test_name, lo.ordered_at,
                   p.id AS patient_id, p.first_name, p.last_name
            FROM lab_orders lo
            JOIN patients p ON p.id = lo.patient_id
            LEFT JOIN lab_results lr ON lr.lab_order_id = lo.id
            WHERE DATE(lo.ordered_at) = :date AND COALESCE(lr.status, 'pending') = 'pending'
            ORDER BY lo.ordered_at DESC
            """
        ),
        {"date": date},
    )
    return [dict(row._mapping) for row in result]
