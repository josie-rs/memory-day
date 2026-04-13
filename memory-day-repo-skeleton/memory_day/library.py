"""某年今日内容库读写。"""

import json
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional

from config import MEMORY_LIBRARY_PATH

logger = logging.getLogger(__name__)

MemoryLibrary = Dict[str, List[dict]]


def get_memory_library_path() -> Path:
    return MEMORY_LIBRARY_PATH


def load_memory_library() -> MemoryLibrary:
    if not MEMORY_LIBRARY_PATH.exists():
        return {}
    try:
        with open(MEMORY_LIBRARY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_memory_library(data: MemoryLibrary):
    with open(MEMORY_LIBRARY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_memory_entries_for_date(month: int, day: int) -> List[dict]:
    date_key = f"{month:02d}-{day:02d}"
    library = load_memory_library()
    return list(library.get(date_key, []))


def get_random_memory_entry(month: int, day: int) -> Optional[dict]:
    entries = get_memory_entries_for_date(month, day)
    if not entries:
        return None
    return random.choice(entries)


def remove_memory_entry(month: int, day: int, photo_id: str) -> bool:
    """从某年今日内容库删除指定条目。"""
    date_key = f"{month:02d}-{day:02d}"
    library = load_memory_library()
    entries = library.get(date_key, [])
    new_entries = [e for e in entries if e.get("photo_id") != photo_id]
    if len(new_entries) == len(entries):
        return False
    if new_entries:
        library[date_key] = new_entries
    else:
        del library[date_key]
    save_memory_library(library)
    logger.info(f"删除某年今日条目: {date_key} - {photo_id}")
    return True


def add_memory_entry(month: int, day: int, entry: dict) -> bool:
    date_key = f"{month:02d}-{day:02d}"
    library = load_memory_library()

    if date_key not in library:
        library[date_key] = []

    existing_ids = {existing["photo_id"] for existing in library[date_key]}
    if entry["photo_id"] in existing_ids:
        logger.info(f"照片已存在，跳过: {entry['photo_id']}")
        return False

    library[date_key].append(entry)
    save_memory_library(library)
    logger.info(f"添加某年今日内容: {date_key} - {entry['filename']}")
    return True
