from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    BILLING = "billing"


TOOL_PERMISSIONS: dict[str, set[Role]] = {
    "get_today_patient_count": {Role.ADMIN, Role.DOCTOR, Role.NURSE},
    "get_today_appointment_count": {Role.ADMIN, Role.DOCTOR, Role.NURSE},
    "get_pending_lab_results": {Role.ADMIN, Role.DOCTOR, Role.NURSE},
    "get_unpaid_invoice_count": {Role.ADMIN, Role.BILLING},
    "get_today_revenue": {Role.ADMIN, Role.BILLING},
    "search_patient_by_name": {Role.ADMIN, Role.DOCTOR, Role.NURSE},
    "get_patient_summary": {Role.ADMIN, Role.DOCTOR, Role.NURSE},
    "get_doctor_schedule": {Role.ADMIN, Role.DOCTOR, Role.NURSE},
    "get_lab_pending_by_date": {Role.ADMIN, Role.DOCTOR, Role.NURSE},
}


def can_call_tool(role: str, tool_name: str) -> bool:
    try:
        parsed_role = Role(role)
    except ValueError:
        return False
    return parsed_role in TOOL_PERMISSIONS.get(tool_name, set())


def can_view_sensitive_patient_data(role: str) -> bool:
    return role in {Role.ADMIN.value, Role.DOCTOR.value}
