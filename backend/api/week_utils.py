"""
Week Utils
----------
22 марта 2026 (воскресенье) — конец ВЕРХНЕЙ недели.
23 марта 2026 (понедельник) — начало НИЖНЕЙ (чётной) недели.

odd  = верхняя (нечётная)
even = нижняя  (чётная)
"""

from datetime import date, timedelta

# Понедельник недели 23 марта 2026 = НИЖНЯЯ (even)
ANCHOR_MONDAY = date(2026, 3, 23)
ANCHOR_IS_EVEN = True


def get_monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def is_even_week(d: date | None = None) -> bool:
    if d is None:
        d = date.today()
    diff_weeks = (get_monday(d) - ANCHOR_MONDAY).days // 7
    return (diff_weeks % 2 == 0) if ANCHOR_IS_EVEN else (diff_weeks % 2 != 0)


def get_week_type(d: date | None = None) -> str:
    """'even' = нижняя, 'odd' = верхняя"""
    return "even" if is_even_week(d) else "odd"


def get_week_info(d: date | None = None) -> dict:
    if d is None:
        d = date.today()
    even = is_even_week(d)
    monday = get_monday(d)
    return {
        "date": d.isoformat(),
        "week_start": monday.isoformat(),
        "week_end": (monday + timedelta(days=6)).isoformat(),
        "is_even": even,
        "week_type": "even" if even else "odd",
        "label": "Нижняя" if even else "Верхняя",
        "label_full": "Нижняя неделя" if even else "Верхняя неделя",
    }
