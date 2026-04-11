"""某年今日照片能力。"""

import logging
import os
import plistlib
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from plistlib import UID
from typing import Any, Dict, List, Optional

from config import MEMORY_EXPORT_DIR, PHOTOS_DB_PATH

logger = logging.getLogger(__name__)

EXPORT_DIR = Path(MEMORY_EXPORT_DIR)
PHOTOS_DB = Path(PHOTOS_DB_PATH)
APPLE_EPOCH_OFFSET = 978307200
MIN_PHOTO_DIMENSION = 1000


def _compute_aesthetic_score(photo: Dict) -> float:
    weights = {
        "composition": 0.20,
        "lighting": 0.18,
        "color": 0.15,
        "subject": 0.12,
        "framing": 0.10,
        "focus": 0.10,
        "timing": 0.08,
        "symmetry": 0.07,
    }
    score = 0.0
    score += max(photo.get("composition", 0) or 0, 0) * weights["composition"]
    score += max(photo.get("lighting", 0) or 0, 0) * weights["lighting"]
    score += max(photo.get("color", 0) or 0, 0) * weights["color"]
    score += max(photo.get("subject", 0) or 0, 0) * weights["subject"]
    score += max(photo.get("framing", 0) or 0, 0) * weights["framing"]
    score += max(photo.get("focus", 0) or 0, 0) * weights["focus"]
    score += max(photo.get("timing", 0) or 0, 0) * weights["timing"]
    score += max(photo.get("symmetry", 0) or 0, 0) * weights["symmetry"]
    if photo.get("favorite"):
        score += 0.15
    return round(score, 4)


def _normalize_photo_id(photo_id: str) -> str:
    return photo_id.split("/", 1)[0]


def _resolve_nskeyed_value(value: Any, objects: List[Any]) -> Any:
    if isinstance(value, UID):
        return objects[value.data]
    return value


def _clean_location_component(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned or cleaned == "$null" or cleaned == "CN":
            return None
        return cleaned
    return None


def _normalize_place_name(place: Optional[str]) -> Optional[str]:
    place = _clean_location_component(place)
    if not place:
        return None
    if "(" in place:
        place = place.split("(", 1)[0].strip()
    if "（" in place:
        place = place.split("（", 1)[0].strip()
    suffixes = ["西南门", "西北门", "东南门", "东北门", "南门", "北门", "东门", "西门"]
    for suffix in suffixes:
        if place.endswith(suffix):
            place = place[: -len(suffix)].strip()
            break
    return place or None


def _simplify_city_name(city: Optional[str]) -> Optional[str]:
    city = _clean_location_component(city)
    if not city:
        return None
    if city.endswith("市"):
        return city[:-1]
    return city


def _format_location_text(city: Optional[str], place: Optional[str]) -> Optional[str]:
    city = _simplify_city_name(city)
    place = _normalize_place_name(place)
    if place == city:
        place = None
    if city and place:
        return f"{city}-{place}"
    return city or place


def _extract_place_candidates(place_infos: Any, objects: List[Any]) -> List[str]:
    candidates = []
    if not isinstance(place_infos, dict):
        return candidates
    for item_uid in place_infos.get("NS.objects", []):
        item = _resolve_nskeyed_value(item_uid, objects)
        if not isinstance(item, dict):
            continue
        name = _clean_location_component(_resolve_nskeyed_value(item.get("name"), objects))
        if name:
            candidates.append(name)
    return candidates


def _extract_location_from_reverse_geocode_blob(blob: bytes) -> Optional[str]:
    archive = plistlib.loads(blob)
    objects = archive.get("$objects", [])
    if not objects:
        return None

    root_uid = archive.get("$top", {}).get("root")
    root = _resolve_nskeyed_value(root_uid, objects)
    if not isinstance(root, dict):
        return None

    postal = _resolve_nskeyed_value(root.get("postalAddress"), objects)
    address_string = _clean_location_component(_resolve_nskeyed_value(root.get("addressString"), objects))

    city = district = street = country = None
    if isinstance(postal, dict):
        city = _clean_location_component(_resolve_nskeyed_value(postal.get("_city"), objects))
        district = _clean_location_component(_resolve_nskeyed_value(postal.get("_subLocality"), objects))
        street = _clean_location_component(_resolve_nskeyed_value(postal.get("_street"), objects))
        country = _clean_location_component(_resolve_nskeyed_value(postal.get("_country"), objects))

    map_item = _resolve_nskeyed_value(root.get("mapItem"), objects)
    sorted_infos = final_infos = None
    if isinstance(map_item, dict):
        sorted_infos = _resolve_nskeyed_value(map_item.get("sortedPlaceInfos"), objects)
        final_infos = _resolve_nskeyed_value(map_item.get("finalPlaceInfos"), objects)

    excluded = {value for value in [city, district, street, country] if value}
    primary_place = None
    for candidate in _extract_place_candidates(sorted_infos, objects):
        if candidate not in excluded:
            primary_place = candidate
            break
    if not primary_place:
        for candidate in _extract_place_candidates(final_infos, objects):
            if candidate not in excluded:
                primary_place = candidate
                break

    return (
        _format_location_text(city, primary_place)
        or _format_location_text(city, district)
        or _format_location_text(city, None)
        or _format_location_text(None, address_string)
    )


def get_photo_capture_time(photo_id: str) -> Optional[str]:
    if not PHOTOS_DB.exists():
        logger.error(f"Photos 数据库不存在: {PHOTOS_DB}")
        return None
    try:
        conn = sqlite3.connect(f"file:{PHOTOS_DB}?mode=ro", uri=True)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT strftime('%Y-%m-%d %H:%M', datetime(ZDATECREATED + ?, 'unixepoch', 'localtime'))
            FROM ZASSET
            WHERE ZUUID = ?
            """,
            (APPLE_EPOCH_OFFSET, _normalize_photo_id(photo_id)),
        )
        row = cursor.fetchone()
        conn.close()
        if row and row[0]:
            capture_dt = datetime.strptime(row[0], "%Y-%m-%d %H:%M")
            return f"{capture_dt.year}年{capture_dt.month}月{capture_dt.day}日 {capture_dt:%H:%M}"
    except Exception as e:
        logger.warning(f"读取照片拍摄时间失败: {e}")
    return None


def get_photo_capture_location(photo_id: str) -> Optional[str]:
    if not PHOTOS_DB.exists():
        logger.error(f"Photos 数据库不存在: {PHOTOS_DB}")
        return None
    try:
        conn = sqlite3.connect(f"file:{PHOTOS_DB}?mode=ro", uri=True)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT aa.ZREVERSELOCATIONDATA
            FROM ZASSET a
            LEFT JOIN ZADDITIONALASSETATTRIBUTES aa ON aa.ZASSET = a.Z_PK
            WHERE a.ZUUID = ?
            """,
            (_normalize_photo_id(photo_id),),
        )
        row = cursor.fetchone()
        conn.close()
        if row and row[0]:
            return _extract_location_from_reverse_geocode_blob(row[0])
    except Exception as e:
        logger.warning(f"读取照片拍摄地点失败: {e}")
    return None


def discover_photos_for_date(month: int, day: int, top_n: int = 0) -> List[Dict]:
    if not PHOTOS_DB.exists():
        logger.error(f"Photos 数据库不存在: {PHOTOS_DB}")
        return []
    try:
        conn = sqlite3.connect(f"file:{PHOTOS_DB}?mode=ro", uri=True)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                a.ZUUID,
                a.ZFILENAME,
                CAST(strftime('%Y', datetime(a.ZDATECREATED + ?, 'unixepoch', 'localtime')) AS INTEGER) as year,
                a.ZFAVORITE,
                a.ZWIDTH,
                a.ZHEIGHT,
                COALESCE(c.ZPLEASANTCOMPOSITIONSCORE, 0),
                COALESCE(c.ZPLEASANTLIGHTINGSCORE, 0),
                COALESCE(c.ZHARMONIOUSCOLORSCORE, 0),
                COALESCE(c.ZWELLCHOSENSUBJECTSCORE, 0),
                COALESCE(c.ZWELLFRAMEDSUBJECTSCORE, 0),
                COALESCE(c.ZSHARPLYFOCUSEDSUBJECTSCORE, 0),
                COALESCE(c.ZWELLTIMEDSHOTSCORE, 0),
                COALESCE(c.ZPLEASANTSYMMETRYSCORE, 0),
                COALESCE(c.ZINTERESTINGSUBJECTSCORE, 0)
            FROM ZASSET a
            LEFT JOIN ZCOMPUTEDASSETATTRIBUTES c ON c.ZASSET = a.Z_PK
            WHERE a.ZTRASHEDSTATE = 0
                AND a.ZHIDDEN = 0
                AND a.ZKIND = 0
                AND a.ZISDETECTEDSCREENSHOT = 0
                AND a.ZWIDTH >= ?
                AND a.ZHEIGHT >= ?
                AND CAST(strftime('%m', datetime(a.ZDATECREATED + ?, 'unixepoch', 'localtime')) AS INTEGER) = ?
                AND CAST(strftime('%d', datetime(a.ZDATECREATED + ?, 'unixepoch', 'localtime')) AS INTEGER) = ?
            """,
            (
                APPLE_EPOCH_OFFSET,
                MIN_PHOTO_DIMENSION,
                MIN_PHOTO_DIMENSION,
                APPLE_EPOCH_OFFSET,
                month,
                APPLE_EPOCH_OFFSET,
                day,
            ),
        )

        photos = []
        for row in cursor.fetchall():
            photo = {
                "photo_id": row[0],
                "filename": row[1],
                "year": row[2],
                "favorite": bool(row[3]),
                "width": row[4],
                "height": row[5],
                "composition": row[6],
                "lighting": row[7],
                "color": row[8],
                "subject": row[9],
                "framing": row[10],
                "focus": row[11],
                "timing": row[12],
                "symmetry": row[13],
                "interesting": row[14],
            }
            photo["aesthetic_score"] = _compute_aesthetic_score(photo)
            photos.append(photo)

        conn.close()
        photos.sort(key=lambda p: p["aesthetic_score"], reverse=True)
        total = len(photos)
        if top_n > 0:
            photos = photos[:top_n]
        logger.info(
            f"发现 {month}月{day}日 的照片 {total} 张"
            f"（过滤截图/视频/小图后），返回 top {len(photos)}"
        )
        return photos
    except Exception as e:
        logger.error(f"Photos 数据库查询异常: {e}")
        return []


def export_photo(photo_id: str) -> Optional[str]:
    os.makedirs(EXPORT_DIR, exist_ok=True)
    existing_files = set(os.listdir(EXPORT_DIR))
    script = f'''
tell application "Photos"
    set targetFolder to POSIX file "{EXPORT_DIR}" as alias
    set targetItem to media item id "{photo_id}"
    export {{targetItem}} to targetFolder
    return filename of targetItem
end tell
'''
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            logger.error(f"照片导出失败: {result.stderr}")
            return None
        fname = result.stdout.strip()
        base_name = os.path.splitext(fname)[0]

        current_files = sorted(os.listdir(EXPORT_DIR))
        new_files = [file_name for file_name in current_files if file_name not in existing_files]
        for file_name in new_files:
            if file_name == fname or file_name.startswith(f"{base_name} ("):
                exported_path = str(EXPORT_DIR / file_name)
                logger.info(f"照片导出成功: {exported_path}")
                return exported_path

        exact_path = EXPORT_DIR / fname
        if exact_path.exists():
            exported_path = str(exact_path)
            logger.info(f"照片导出成功: {exported_path}")
            return exported_path

        fallback_matches = [
            file_name for file_name in current_files
            if file_name == fname or file_name.startswith(f"{base_name} (")
        ]
        if fallback_matches:
            exported_path = str(EXPORT_DIR / sorted(fallback_matches)[-1])
            logger.warning(f"照片导出回退匹配: {exported_path}")
            return exported_path

        logger.error(f"导出后未找到文件: {fname}")
        return None
    except subprocess.TimeoutExpired:
        logger.error("照片导出超时")
        return None
    except Exception as e:
        logger.error(f"照片导出异常: {e}")
        return None


def cleanup_exported_photo(file_path: str):
    try:
        if file_path and os.path.exists(file_path) and str(EXPORT_DIR) in file_path:
            os.remove(file_path)
            logger.info(f"已清理临时照片: {file_path}")
    except Exception as e:
        logger.warning(f"清理临时照片失败（不影响推送）: {e}")
