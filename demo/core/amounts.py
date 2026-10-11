"""Parse baht amounts that may be stored as numbers or as formatted text.

claims.claim_amount holds some values as text such as "11,925.00". A missing
amount stays None so validation can report it; it is never treated as zero.
"""


class AmountParseError(ValueError):
    """Raised when an amount is text that is not a number."""


def parse_amount(raw: float | int | str | None) -> float | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    cleaned = raw.strip().replace(",", "")
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError as exc:
        raise AmountParseError(f"{raw!r} is not a number") from exc
