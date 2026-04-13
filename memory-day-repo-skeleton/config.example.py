"""
公开版本示例配置。
复制为 config.py 后再填写真实值。
"""

from pathlib import Path

BASE_DIR = Path(__file__).parent
MEMORY_LIBRARY_PATH = BASE_DIR / "content" / "memory_library.json"
MEMORY_EXPORT_DIR = Path("/tmp/memory-day-exports")
PHOTOS_DB_PATH = Path.home() / "Pictures" / "Photos Library.photoslibrary" / "database" / "Photos.sqlite"
