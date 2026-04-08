"""Billing domain utilities."""


def bill_totals(*, subtotal: float, tax_rate: float, service_charge_rate: float) -> dict[str, float]:
    if subtotal < 0:
        raise ValueError("Subtotal cannot be negative")
    tax_amount = round(subtotal * tax_rate, 2)
    service_charge = round(subtotal * service_charge_rate, 2)
    total_amount = round(subtotal + tax_amount + service_charge, 2)
    return {
        "subtotal": round(subtotal, 2),
        "tax_amount": tax_amount,
        "service_charge": service_charge,
        "total_amount": total_amount,
    }


def apply_settlement(*, paid_amount: float, incoming_amount: float, total_amount: float) -> tuple[float, str]:
    next_paid = round(paid_amount + incoming_amount, 2)
    if next_paid > total_amount:
        raise ValueError("Settlement exceeds bill amount")
    if next_paid == total_amount:
        return next_paid, "paid"
    return next_paid, "partially_paid"
