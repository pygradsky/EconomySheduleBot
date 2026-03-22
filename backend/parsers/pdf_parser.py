"""
PDF Schedule Parser
-------------------
Format:
- Column 0: day (vertical letters)
- Column 1: time slot — присутствует только в строке ВЕРХНЕЙ недели,
            следующая строка без времени = НИЖНЯЯ неделя
- Columns 2+: lessons per group

Week assignment rule:
  row has time  → верхняя (odd)
  row has no time but follows a time row → нижняя (even)
"""

import re
import hashlib
from pathlib import Path
from typing import Optional
from loguru import logger

try:
    import pdfplumber

    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

from backend.models.schedule import Lesson, DaySchedule, GroupSchedule, CourseSchedule

DAYS_RU = ["ПОНЕДЕЛЬНИК", "ВТОРНИК", "СРЕДА", "ЧЕТВЕРГ", "ПЯТНИЦА"]
DAYS_RU_DISPLAY = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"]
DAYS_EN = ["monday", "tuesday", "wednesday", "thursday", "friday"]

LESSON_TYPE_MAP = {"лек": "lecture", "пр": "practice", "сем": "seminar", "лаб": "lab"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def pdf_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_str(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def normalize_time(raw: str) -> tuple[str, str]:
    """'09.00-\\n10.35' → ('09:00', '10:35')"""
    raw = raw.replace("\n", " ").strip()
    raw = re.sub(r'(\d{2})\.(\d{2})', r'\1:\2', raw)
    parts = re.findall(r'\d{2}:\d{2}', raw)
    if len(parts) >= 2:
        return parts[0], parts[1]
    if len(parts) == 1:
        return parts[0], ""
    return "", ""


def detect_lesson_type(prefix: str) -> str:
    return LESSON_TYPE_MAP.get(prefix.lower(), "other")


def split_lessons(cell: str) -> list[str]:
    lines = [l.strip() for l in cell.strip().split("\n") if l.strip()]
    blocks, current = [], []
    for line in lines:
        if re.match(r'^(лек|пр|сем|лаб)\.', line, re.IGNORECASE) and current:
            blocks.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks if blocks else [cell.strip()]


def parse_lesson_text(raw: str, time_start: str, time_end: str,
                      week_type: Optional[str]) -> Optional[Lesson]:
    lines = [l.strip() for l in raw.strip().split("\n") if l.strip()]
    if not lines:
        return None

    first = lines[0]
    lesson_type = "other"
    subject = first

    m = re.match(r'^(лек|пр|сем|лаб)\.(.*)', first, re.IGNORECASE)
    if m:
        lesson_type = detect_lesson_type(m.group(1))
        subject = m.group(2).strip()

    rest = " ".join(lines[1:]) if len(lines) > 1 else ""
    room = None
    room_match = re.search(r'\b(\d{2}-[\w]+)\s*$', rest)
    if room_match:
        room = room_match.group(1)
        teacher = rest[:room_match.start()].strip()
    else:
        teacher = rest.strip()

    teacher = re.sub(r'[,;.\s]+$', '', teacher).strip() or None

    if not subject or len(subject) < 2:
        return None

    return Lesson(
        time_start=time_start,
        time_end=time_end,
        subject=subject[:150],
        teacher=teacher[:100] if teacher else None,
        room=room,
        lesson_type=lesson_type,
        week_type=week_type,  # "odd"=верхняя | "even"=нижняя | None=обе
    )


# ── Table parser ───────────────────────────────────────────────────────────────

def parse_table(table: list[list[str]], course: int) -> dict[str, dict[str, list[Lesson]]]:
    if not table or len(table) < 2:
        return {}

    # Find header row
    header_row = table[0]
    header_idx = 0
    for i, row in enumerate(table[:4]):
        joined = " ".join(str(c or "") for c in row)
        if "Дни" in joined or "Часы" in joined or re.search(r'[А-ЯЁ]{2,3}\s*\d{2}-\d{2}', joined):
            header_row = row
            header_idx = i
            break

    # Group names from columns 2+
    groups: list[Optional[str]] = []
    for cell in header_row[2:]:
        g = (cell or "").replace("\n", " ").strip()
        groups.append(g if g and g != "None" else None)

    if not any(groups):
        logger.warning("No group names found in header row")
        return {}

    result: dict[str, dict[str, list[Lesson]]] = {
        g: {d: [] for d in DAYS_RU} for g in groups if g
    }

    current_day = ""
    current_ts = ""  # time_start
    current_te = ""  # time_end
    last_had_time = False  # True if previous data row had a time cell

    for row in table[header_idx + 1:]:
        if not row or len(row) < 3:
            continue

        # Detect day
        day_cell = (row[0] or "").replace("\n", "").strip().upper()
        if day_cell in DAYS_RU:
            current_day = day_cell
            last_had_time = False

        # Detect time — column 1
        time_raw = (row[1] or "").strip()
        has_time = bool(re.search(r'\d{1,2}[.:]\d{2}', time_raw))

        if has_time:
            current_ts, current_te = normalize_time(time_raw)
            week_type = "odd"
            last_had_time = True
            last_time_row_idx = len(result)
        else:
            if last_had_time:
                week_type = "even"
            else:
                week_type = None

        if not current_day or not current_ts:
            continue

        for i, cell in enumerate(row[2:]):
            if i >= len(groups):
                break
            group = groups[i]
            if not group or not cell or not cell.strip():
                continue

            stripped = cell.replace("\n", "").strip()
            if len(stripped) <= 2:
                continue
            # skip vertical day text artifacts
            if len(re.findall(r'(?<!\w)[А-ЯЁA-Z](?!\w)', stripped)) > 8:
                continue

            for lesson_raw in split_lessons(cell):
                lesson = parse_lesson_text(lesson_raw, current_ts, current_te, week_type)
                if lesson:
                    result[group][current_day].append(lesson)

    for group_lessons in result.values():
        for day_lessons in group_lessons.values():
            from itertools import groupby
            by_time: dict[str, list] = {}
            for l in day_lessons:
                by_time.setdefault(l.time_start, []).append(l)
            for ts, lessons in by_time.items():
                types = {l.week_type for l in lessons}
                if types == {"odd"}:
                    for l in lessons:
                        l.week_type = None

    return result


# ── Main entry point ───────────────────────────────────────────────────────────

def parse_pdf(path: Path, course: int) -> CourseSchedule:
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    if not HAS_PDFPLUMBER:
        raise ImportError("pdfplumber is not installed")

    logger.info(f"Parsing PDF: {path} (course {course})")
    file_hash = pdf_hash(path)
    merged: dict[str, dict[str, list[Lesson]]] = {}

    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            for table in (page.extract_tables() or []):
                if not table or len(table[0]) < 3:
                    continue
                for group, day_map in parse_table(table, course).items():
                    if group not in merged:
                        merged[group] = {d: [] for d in DAYS_RU}
                    for day, lessons in day_map.items():
                        merged[group][day].extend(lessons)

    if not merged:
        logger.warning(f"No schedule data extracted from {path}")
        return CourseSchedule(course=course, groups=[], schedules={}, pdf_hash=file_hash)

    schedules: dict[str, GroupSchedule] = {}
    for group_name, day_map in merged.items():
        days = []
        for day_upper, day_display, day_en in zip(DAYS_RU, DAYS_RU_DISPLAY, DAYS_EN):
            lessons = day_map.get(day_upper, [])
            if lessons:
                days.append(DaySchedule(day=day_display, day_en=day_en, lessons=lessons))
        if days:
            content = str([(d.day, [(l.subject,) for l in d.lessons]) for d in days])
            schedule_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
            schedules[group_name] = GroupSchedule(
                group=group_name, course=course, days=days, hash=schedule_hash
            )

    groups = sorted(schedules.keys())
    logger.info(f"Parsed {len(groups)} groups: {groups}")
    return CourseSchedule(course=course, groups=groups, schedules=schedules, pdf_hash=file_hash)


def get_course_from_group(group: str) -> int:
    m = re.search(r'-(\d{2})$', group)
    if m:
        return {25: 1, 24: 2, 23: 3, 22: 4}.get(int(m.group(1)), 0)
    return 0


def generate_demo_schedule(course: int) -> CourseSchedule:
    import random
    random.seed(course * 42)
    subjects = {
        1: ["Математический анализ", "История России", "Философия", "Иностранный язык", "БЖД"],
        2: ["Микроэкономика", "Статистика", "Менеджмент", "Право", "Цифровые технологии"],
        3: ["Макроэкономика", "Финансы и кредит", "Бухучёт", "Маркетинг", "Эконометрика"],
        4: ["Стратегический менеджмент", "Международная экономика", "Налогообложение", "Аудит", "ВКР"],
    }
    groups_map = {1: ["ДЭ 10-25", "ДЭ 11-25"], 2: ["ДЭ 01-24", "ДЭ 02-24"],
                  3: ["ДЭ 01-23", "ДЭ 02-23"], 4: ["ДЭ 01-22"]}
    time_slots = [("09:00", "10:35"), ("10:55", "12:30"), ("13:00", "14:35"), ("14:55", "16:30")]
    teachers = ["Иванов А.А.", "Петрова Б.В.", "Сидоров В.Г."]
    rooms = ["01-407", "12-220", "28-316"]
    types = ["lecture", "practice", "seminar"]
    week_types = ["odd", "even", None]

    schedules = {}
    for group in groups_map.get(course, ["ДЭ 01-25"]):
        days = []
        for day_display, day_en in zip(DAYS_RU_DISPLAY, DAYS_EN):
            slots = sorted(random.sample(time_slots, random.randint(2, 4)))
            lessons = [
                Lesson(time_start=ts, time_end=te,
                       subject=random.choice(subjects.get(course, subjects[1])),
                       teacher=random.choice(teachers), room=random.choice(rooms),
                       lesson_type=random.choice(types),
                       week_type=random.choice(week_types))
                for ts, te in slots
            ]
            days.append(DaySchedule(day=day_display, day_en=day_en, lessons=lessons))
        content = str([(d.day, [l.subject for l in d.lessons]) for d in days])
        schedule_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        schedules[group] = GroupSchedule(group=group, course=course, days=days, hash=schedule_hash)

    file_hash = hashlib.sha256(f"demo-course-{course}".encode()).hexdigest()
    return CourseSchedule(course=course, groups=sorted(schedules.keys()),
                          schedules=schedules, pdf_hash=file_hash)
