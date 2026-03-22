"""
Schedule Service
----------------
Loads all PDFs on startup, caches parsed data,
and provides fast access to schedule information.
"""

import asyncio
from pathlib import Path
from loguru import logger
from backend.config import settings
from backend.cache.memory_cache import cache, hash_str
from backend.models.schedule import CourseSchedule, GroupSchedule
from backend.parsers.pdf_parser import parse_pdf, generate_demo_schedule, pdf_hash


class ScheduleService:
    CACHE_KEY_COURSE = "course:{course}"
    CACHE_KEY_GROUP = "group:{course}:{group}"
    CACHE_KEY_GROUPS_LIST = "groups_list:{course}"
    CACHE_KEY_PDF_HASH = "pdf_hash:{course}"

    def __init__(self):
        self._loaded_courses: set[int] = set()

    def _find_pdf(self, course: int) -> Path | None:
        """
        Find any PDF file inside the course directory.
        Doesn't care about the filename — takes the first PDF found.
        E.g. economy_1.pdf, schedule_1.pdf, расписание.pdf — всё подойдёт.
        """
        course_dir = settings.data_path / str(course)
        if not course_dir.exists():
            logger.warning(f"Course {course}: directory not found → {course_dir}")
            return None
        pdfs = sorted(course_dir.glob("*.pdf"))
        if pdfs:
            logger.info(f"Course {course}: found PDF → {pdfs[0].name}")
            if len(pdfs) > 1:
                logger.warning(
                    f"Course {course}: multiple PDFs found, using first: "
                    + ", ".join(p.name for p in pdfs)
                )
        return pdfs[0] if pdfs else None

    async def load_all(self) -> None:
        """Load all PDFs from data directory on startup."""
        data_path = settings.data_path
        logger.info(f"Loading schedules from: {data_path.resolve()}")

        tasks = [self._load_course(course) for course in range(1, 5)]
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"Loaded courses: {sorted(self._loaded_courses)}")

    async def _load_course(self, course: int) -> None:
        """Load a single course PDF into cache."""
        pdf_path = self._find_pdf(course)

        cache_key = self.CACHE_KEY_COURSE.format(course=course)
        hash_key  = self.CACHE_KEY_PDF_HASH.format(course=course)

        if pdf_path is not None:
            current_hash = pdf_hash(pdf_path)
            cached_hash  = cache.get(hash_key)

            if cached_hash == current_hash and cache.has(cache_key):
                logger.info(f"Course {course}: using cached data (hash match)")
                self._loaded_courses.add(course)
                return

            try:
                logger.info(f"Course {course}: parsing {pdf_path.name} ...")
                course_schedule = await asyncio.to_thread(parse_pdf, pdf_path, course)
                self._store_course(course, course_schedule, current_hash)
                logger.info(
                    f"Course {course}: loaded {len(course_schedule.groups)} groups"
                )
            except Exception as e:
                logger.error(f"Course {course}: parse failed ({e}), falling back to demo")
                await self._load_demo(course)
        else:
            logger.warning(f"Course {course}: no PDF found in data/schedule/{course}/, using demo data")
            await self._load_demo(course)

    async def _load_demo(self, course: int) -> None:
        """Load demo schedule when PDF is missing or broken."""
        demo = await asyncio.to_thread(generate_demo_schedule, course)
        demo_hash = hash_str(f"demo-{course}")
        self._store_course(course, demo, demo_hash)
        logger.info(f"Course {course}: demo schedule loaded ({len(demo.groups)} groups)")

    def _store_course(self, course: int, schedule: CourseSchedule, file_hash: str) -> None:
        """Store course schedule in cache."""
        cache.set(self.CACHE_KEY_COURSE.format(course=course), schedule.model_dump())
        cache.set(self.CACHE_KEY_PDF_HASH.format(course=course), file_hash)
        cache.set(self.CACHE_KEY_GROUPS_LIST.format(course=course), schedule.groups)

        for group_name, group_schedule in schedule.schedules.items():
            group_key = self.CACHE_KEY_GROUP.format(course=course, group=group_name)
            cache.set(group_key, group_schedule.model_dump())

        self._loaded_courses.add(course)

    async def get_groups(self, course: int) -> list[str]:
        key = self.CACHE_KEY_GROUPS_LIST.format(course=course)
        groups = cache.get(key)
        if groups is None:
            await self._load_course(course)
            groups = cache.get(key) or []
        return groups

    async def get_group_schedule(self, course: int, group: str) -> GroupSchedule | None:
        key = self.CACHE_KEY_GROUP.format(course=course, group=group)
        data = cache.get(key)
        if data is None:
            await self._load_course(course)
            data = cache.get(key)
        if data is None:
            return None
        return GroupSchedule(**data)

    async def get_course_schedule(self, course: int) -> CourseSchedule | None:
        key = self.CACHE_KEY_COURSE.format(course=course)
        data = cache.get(key)
        if data is None:
            await self._load_course(course)
            data = cache.get(key)
        if data is None:
            return None
        return CourseSchedule(**data)

    def get_loaded_courses(self) -> list[int]:
        return sorted(self._loaded_courses)

    async def reload_course(self, course: int) -> None:
        """Force reload a specific course (e.g. after PDF update)."""
        cache.delete(self.CACHE_KEY_PDF_HASH.format(course=course))
        await self._load_course(course)

    def cache_stats(self) -> dict:
        return cache.stats()


# Global service singleton
schedule_service = ScheduleService()
