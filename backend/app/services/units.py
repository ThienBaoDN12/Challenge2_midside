"""Deterministic quantity / money maths (FR-40, NFR-05). Never delegated to AI."""
from decimal import ROUND_HALF_UP, Decimal

KG_PER = {"ton": Decimal(1000), "kg": Decimal(1)}


def to_kg(qty, unit: str) -> Decimal:
    return Decimal(str(qty)) * KG_PER[unit]


def price_per_kg(price, price_unit: str) -> tuple[Decimal, str]:
    """'USD/ton' -> (price per kg, 'USD')."""
    currency, per = price_unit.split("/")
    return Decimal(str(price)) / KG_PER[per], currency


def total_value(qty, qty_unit: str, price, price_unit: str) -> tuple[Decimal, str]:
    per_kg, currency = price_per_kg(price, price_unit)
    total = (to_kg(qty, qty_unit) * per_kg).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return total, currency


def fmt_money(amount: Decimal, currency: str) -> str:
    # "43.000 USD" style used in the spec's policy messages
    whole = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if whole.endswith(",00"):
        whole = whole[:-3]
    return f"{whole} {currency}"
