"""
FastAPI Routes
"""

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from backend.api.schedule_service import schedule_service
from backend.api.week_utils import get_week_info, is_even_week

router = APIRouter(prefix="/api/v1", tags=["schedule"])


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "loaded_courses": schedule_service.get_loaded_courses(),
        "cache": schedule_service.cache_stats(),
    }


@router.get("/week")
async def get_week():
    """Return current week parity info."""
    return get_week_info()


@router.get("/courses")
async def get_courses():
    return {"courses": [1, 2, 3, 4]}


@router.get("/courses/{course}/groups")
async def get_groups(
    course: int,
    search: str = Query(default="", description="Filter groups by name"),
):
    if course not in range(1, 5):
        raise HTTPException(status_code=400, detail="Course must be between 1 and 4")
    groups = await schedule_service.get_groups(course)
    if search:
        groups = [g for g in groups if search.lower() in g.lower()]
    return {"course": course, "groups": groups, "total": len(groups)}


@router.get("/courses/{course}/groups/{group}/schedule")
async def get_schedule(course: int, group: str):
    if course not in range(1, 5):
        raise HTTPException(status_code=400, detail="Course must be between 1 and 4")
    schedule = await schedule_service.get_group_schedule(course, group)
    if schedule is None:
        raise HTTPException(status_code=404, detail=f"Schedule not found for '{group}'")

    # Attach current week info to response
    week = get_week_info()
    data = schedule.model_dump()
    data["week"] = week
    return data


@router.post("/admin/reload/{course}")
async def reload_course(course: int):
    if course not in range(1, 5):
        raise HTTPException(status_code=400, detail="Invalid course number")
    try:
        await schedule_service.reload_course(course)
        groups = await schedule_service.get_groups(course)
        return {"message": f"Course {course} reloaded", "groups": groups}
    except Exception as e:
        logger.error(f"Reload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
