from pydantic import BaseModel
from typing import Optional


class Lesson(BaseModel):
    time_start: str           # "08:30"
    time_end: str             # "10:00"
    subject: str              # "Математический анализ"
    teacher: Optional[str] = None
    room: Optional[str] = None
    lesson_type: str = "lecture"   # lecture | practice | seminar | lab | other
    week_type: Optional[str] = None  # "odd" | "even" | None (both)
    subgroup: Optional[str] = None


class DaySchedule(BaseModel):
    day: str               # "Понедельник"
    day_en: str            # "monday"
    lessons: list[Lesson]


class GroupSchedule(BaseModel):
    group: str
    course: int
    days: list[DaySchedule]
    hash: str


class CourseSchedule(BaseModel):
    course: int
    groups: list[str]
    schedules: dict[str, GroupSchedule]  # group_name -> GroupSchedule
    pdf_hash: str
