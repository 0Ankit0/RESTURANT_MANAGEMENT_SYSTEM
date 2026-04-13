from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from src.apps.restaurant.models import (
    AccountingExport,
    AccountingExportStatus,
    AttendanceRecord,
    Bill,
    BillStatus,
    CashDrawerSession,
    DayClose,
    DrawerStatus,
    OperationalSeverity,
    Order,
    Refund,
    Shift,
    ShiftStatus,
)


@dataclass
class DayCloseBlocker:
    blocker_code: str
    blocker_type: str
    severity: OperationalSeverity
    count: int
    summary: str
    remediation_action: str
    metadata: dict = field(default_factory=dict)


async def compute_day_close_blockers(*, db: AsyncSession, day_close: DayClose) -> list[DayCloseBlocker]:
    blockers: list[DayCloseBlocker] = []
    window_end = day_close.business_date + timedelta(days=1)

    unpaid_bill_ids = (
        await db.execute(
            select(Bill.id)
            .join(Order, Order.id == Bill.order_id)
            .where(Order.branch_id == day_close.branch_id, Bill.status != BillStatus.PAID)
            .limit(20)
        )
    ).scalars().all()
    unpaid_bills = (
        await db.execute(
            select(func.count(Bill.id))
            .join(Order, Order.id == Bill.order_id)
            .where(Order.branch_id == day_close.branch_id, Bill.status != BillStatus.PAID)
        )
    ).one()[0]
    if unpaid_bills:
        blockers.append(
            DayCloseBlocker(
                blocker_code="unpaid_bills",
                blocker_type="billing",
                severity=OperationalSeverity.CRITICAL,
                count=unpaid_bills,
                summary=f"{unpaid_bills} unpaid bill(s) remain open.",
                remediation_action="resolve_pending_settlement",
                metadata={"branch_id": day_close.branch_id, "bill_ids": unpaid_bill_ids},
            )
        )

    open_drawer_ids = (
        await db.execute(
            select(CashDrawerSession.id).where(
                CashDrawerSession.branch_id == day_close.branch_id,
                CashDrawerSession.status == DrawerStatus.OPEN,
            )
        )
    ).scalars().all()
    open_drawers = (
        await db.execute(
            select(func.count(CashDrawerSession.id)).where(
                CashDrawerSession.branch_id == day_close.branch_id,
                CashDrawerSession.status == DrawerStatus.OPEN,
            )
        )
    ).one()[0]
    if open_drawers:
        blockers.append(
            DayCloseBlocker(
                blocker_code="open_drawers",
                blocker_type="cash_management",
                severity=OperationalSeverity.CRITICAL,
                count=open_drawers,
                summary=f"{open_drawers} cash drawer session(s) are still open.",
                remediation_action="close_drawer",
                metadata={"branch_id": day_close.branch_id, "drawer_session_ids": open_drawer_ids},
            )
        )

    unresolved_refund_ids = (
        await db.execute(
            select(Refund.id).where(
                Refund.branch_id == day_close.branch_id,
                Refund.settlement_id.is_(None),
            )
        )
    ).scalars().all()
    unresolved_refunds = (
        await db.execute(
            select(func.count(Refund.id)).where(
                Refund.branch_id == day_close.branch_id,
                Refund.settlement_id.is_(None),
            )
        )
    ).one()[0]
    if unresolved_refunds:
        blockers.append(
            DayCloseBlocker(
                blocker_code="unresolved_refunds",
                blocker_type="refunds",
                severity=OperationalSeverity.WARNING,
                count=unresolved_refunds,
                summary=f"{unresolved_refunds} refund(s) are pending settlement reconciliation.",
                remediation_action="resolve_refund_settlement",
                metadata={"branch_id": day_close.branch_id, "refund_ids": unresolved_refund_ids},
            )
        )

    pending_export_ids = (
        await db.execute(
            select(AccountingExport.id).where(
                AccountingExport.branch_id == day_close.branch_id,
                AccountingExport.business_date == day_close.business_date,
                AccountingExport.status != AccountingExportStatus.SENT,
            )
        )
    ).scalars().all()
    pending_exports = (
        await db.execute(
            select(func.count(AccountingExport.id)).where(
                AccountingExport.branch_id == day_close.branch_id,
                AccountingExport.business_date == day_close.business_date,
                AccountingExport.status != AccountingExportStatus.SENT,
            )
        )
    ).one()[0]
    if pending_exports:
        blockers.append(
            DayCloseBlocker(
                blocker_code="pending_exports",
                blocker_type="reporting",
                severity=OperationalSeverity.WARNING,
                count=pending_exports,
                summary=f"{pending_exports} accounting export(s) are pending dispatch.",
                remediation_action="rerun_export",
                metadata={"branch_id": day_close.branch_id, "export_ids": pending_export_ids},
            )
        )

    staffing_gap_shift_ids = (
        await db.execute(
            select(Shift.id)
            .where(
                Shift.branch_id == day_close.branch_id,
                Shift.starts_at >= day_close.business_date,
                Shift.starts_at < window_end,
                Shift.status.in_([ShiftStatus.SCHEDULED, ShiftStatus.STARTED]),
            )
            .where(
                Shift.id.notin_(
                    select(AttendanceRecord.shift_id).where(
                        AttendanceRecord.shift_id.is_not(None),
                        AttendanceRecord.branch_id == day_close.branch_id,
                    )
                )
            )
        )
    ).scalars().all()
    staffing_gaps = (
        await db.execute(
            select(func.count(Shift.id))
            .where(
                Shift.branch_id == day_close.branch_id,
                Shift.starts_at >= day_close.business_date,
                Shift.starts_at < window_end,
                Shift.status.in_([ShiftStatus.SCHEDULED, ShiftStatus.STARTED]),
            )
            .where(
                Shift.id.notin_(
                    select(AttendanceRecord.shift_id).where(
                        AttendanceRecord.shift_id.is_not(None),
                        AttendanceRecord.branch_id == day_close.branch_id,
                    )
                )
            )
        )
    ).one()[0]
    if staffing_gaps:
        blockers.append(
            DayCloseBlocker(
                blocker_code="staffing_gaps",
                blocker_type="workforce",
                severity=OperationalSeverity.WARNING,
                count=staffing_gaps,
                summary=f"{staffing_gaps} scheduled shift(s) have no attendance check-in.",
                remediation_action="acknowledge_staffing_override",
                metadata={"branch_id": day_close.branch_id, "shift_ids": staffing_gap_shift_ids},
            )
        )

    return blockers
