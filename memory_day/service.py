"""某年今日服务入口。"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import library, photos

logger = logging.getLogger(__name__)

MemoryPayload = Dict[str, Any]
MemoryEntry = Dict[str, Any]


def get_daily_memory_payload(now: Optional[datetime] = None) -> Optional[MemoryPayload]:
    if now is None:
        now = datetime.now()

    date_key = f"{now.month:02d}-{now.day:02d}"
    entry = library.get_random_memory_entry(now.month, now.day)
    if entry is None:
        logger.info(f"某年今日 {date_key} 无预生成内容")
        return None

    image_path = photos.export_photo(entry["photo_id"])
    if not image_path:
        logger.warning("照片导出失败，跳过某年今日推送")
        return None

    capture_time = entry.get("capture_time")
    if capture_time is None:
        capture_time = photos.get_photo_capture_time(entry["photo_id"])

    capture_location = entry.get("capture_location")

    text = entry["text"]
    if capture_time and capture_location:
        text = f"{text}\n\n（照片拍摄于{capture_time}，{capture_location}）"
    elif capture_time:
        text = f"{text}\n\n（照片拍摄于{capture_time}）"
    elif capture_location:
        text = f"{text}\n\n（照片拍摄于{capture_location}）"

    return {
        "title": entry["title"],
        "text": text,
        "image_path": image_path,
        "photo_id": entry["photo_id"],
        "year": entry.get("year"),
        "capture_time": capture_time,
        "capture_location": capture_location,
    }


def cleanup_daily_memory_payload(payload: Optional[MemoryPayload]):
    if not payload:
        return
    cleanup_daily_memory_image(payload.get("image_path"))


def cleanup_daily_memory_image(image_path: Optional[str]):
    if image_path:
        photos.cleanup_exported_photo(image_path)


def get_memory_library_path() -> Path:
    return library.get_memory_library_path()


def get_memory_entries_for_date(month: int, day: int) -> List[MemoryEntry]:
    return library.get_memory_entries_for_date(month, day)


def discover_memory_candidates(month: int, day: int, top_n: int = 0) -> List[MemoryEntry]:
    return photos.discover_photos_for_date(month, day, top_n=top_n)


def export_memory_candidate(photo_id: str) -> Optional[str]:
    return photos.export_photo(photo_id)


def get_memory_capture_time(photo_id: str) -> Optional[str]:
    return photos.get_photo_capture_time(photo_id)


def get_memory_capture_location(photo_id: str) -> Optional[str]:
    return photos.get_photo_capture_location(photo_id)


def add_memory_library_entry(month: int, day: int, entry: MemoryEntry) -> bool:
    return library.add_memory_entry(month, day, entry)


def prepare_memory_entry_for_date(month: int, day: int, top_n: int = 4) -> Dict[str, Any]:
    existing_entries = get_memory_entries_for_date(month, day)
    result: Dict[str, Any] = {
        "date_key": f"{month:02d}-{day:02d}",
        "library_path": str(get_memory_library_path()),
        "entries": existing_entries,
    }

    if existing_entries:
        result["status"] = "existing"
        result["candidate_photos"] = []
        return result

    candidates = discover_memory_candidates(month, day, top_n=top_n)
    result["candidate_photos"] = candidates
    result["status"] = "ready" if candidates else "no-photo"
    return result
