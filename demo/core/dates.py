"""Convert hospital-specific date strings to ISO 8601 Gregorian dates.

The hospital's declared format (hospitals.date_format) selects the layout and
the calendar. A value that does not match the declared layout is an error, not
a guess.
"""

import re
from datetime import date

BUDDHIST_OFFSET = 543

# Each layout is (regex, group order for year, month, day).
_LAYOUTS = {
    "YYYYMMDD": (re.compile(r"^(\d{2}|\d{4})(\d{2})(\d{2})$"), (1, 2, 3)),
    "DD/MM/YYYY": (re.compile(r"^(\d{2})/(\d{2})/(\d{2}|\d{4})$"), (3, 2, 1)),
    "YYYY-MM-DD": (re.compile(r"^(\d{2}|\d{4})-(\d{2})-(\d{2})$"), (1, 2, 3)),
}


class DateParseError(ValueError):
    """Raised when a raw date does not match the hospital's declared format."""


def parse_hospital_date(raw: str | None, date_format: str) -> date:
    """Parse one raw date string using a hospital's declared date_format.

    date_format looks like "YYYY-MM-DD (พ.ศ.)" or "YYYY-MM-DD". A "(พ.ศ.)"
    suffix means the year is Buddhist Era. A 2-digit year is read as 2500+YY
    for Buddhist Era and 2000+YY otherwise.
    """
    if raw is None or not raw.strip():
        raise DateParseError("empty date")
    layout_name = date_format.split(" ")[0]
    if layout_name not in _LAYOUTS:
        raise DateParseError(f"unknown date format: {date_format}")
    pattern, (y_idx, m_idx, d_idx) = _LAYOUTS[layout_name]

    match = pattern.match(raw.strip())
    if not match:
        raise DateParseError(f"{raw!r} does not match {layout_name}")

    year = int(match.group(y_idx))
    month = int(match.group(m_idx))
    day = int(match.group(d_idx))
    buddhist = "(พ.ศ.)" in date_format

    if year < 100:
        year += 2500 if buddhist else 2000
    if buddhist:
        year -= BUDDHIST_OFFSET

    try:
        return date(year, month, day)
    except ValueError as exc:
        raise DateParseError(f"{raw!r} is not a valid calendar date") from exc
