from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(Enum("admin", "doctor", "nurse", "billing"), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    date_of_birth: Mapped[Date | None] = mapped_column(Date)
    phone: Mapped[str | None] = mapped_column(String(40))
    email: Mapped[str | None] = mapped_column(String(120))
    address: Mapped[str | None] = mapped_column(String(255))
    medical_record_number: Mapped[str | None] = mapped_column(String(80), unique=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    full_name: Mapped[str] = mapped_column(String(120))
    specialty: Mapped[str | None] = mapped_column(String(120))


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    appointment_date: Mapped[Date] = mapped_column(Date, index=True)
    start_time: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(40), default="scheduled")
    reason: Mapped[str | None] = mapped_column(String(255))
    patient: Mapped[Patient] = relationship()
    doctor: Mapped[Doctor] = relationship()


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2))
    amount_paid: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    status: Mapped[str] = mapped_column(String(40), index=True)
    paid_at: Mapped[DateTime | None] = mapped_column(DateTime)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())


class LabOrder(Base):
    __tablename__ = "lab_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    doctor_id: Mapped[int | None] = mapped_column(ForeignKey("doctors.id"))
    test_name: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(40), default="ordered")
    ordered_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())


class LabResult(Base):
    __tablename__ = "lab_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lab_order_id: Mapped[int] = mapped_column(ForeignKey("lab_orders.id"))
    result_text: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="pending", index=True)
    resulted_at: Mapped[DateTime | None] = mapped_column(DateTime)


class AiConversationLog(Base):
    __tablename__ = "ai_conversation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    question: Mapped[str] = mapped_column(Text)
    response: Mapped[str | None] = mapped_column(Text)
    route: Mapped[str | None] = mapped_column(String(40))
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())


class AiToolCallLog(Base):
    __tablename__ = "ai_tool_call_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tool_name: Mapped[str] = mapped_column(String(120))
    arguments_json: Mapped[str] = mapped_column(Text)
    result_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
