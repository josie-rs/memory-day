"""某年今日维护 CLI。"""

import argparse
import json
from datetime import datetime
from typing import Any, Dict, Optional

from memory_day.service import (
    add_memory_library_entry,
    cleanup_daily_memory_image,
    export_memory_candidate,
    get_daily_memory_payload,
    get_memory_capture_location,
    get_memory_capture_time,
    prepare_memory_entry_for_date,
    remove_memory_library_entry,
)


def _parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d")


def _load_entry(args: argparse.Namespace) -> Dict[str, Any]:
    if args.entry_file:
        with open(args.entry_file, "r", encoding="utf-8") as f:
            return json.load(f)
    if args.entry_json:
        return json.loads(args.entry_json)
    raise ValueError("missing entry data")


def _print_json(data: Any):
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="某年今日维护 CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare-date")
    prepare_parser.add_argument("--date", required=True)
    prepare_parser.add_argument("--top-n", type=int, default=4)

    payload_parser = subparsers.add_parser("get-daily-payload")
    payload_parser.add_argument("--date")

    export_parser = subparsers.add_parser("export-photo")
    export_parser.add_argument("--photo-id", required=True)

    cleanup_parser = subparsers.add_parser("cleanup-image")
    cleanup_parser.add_argument("--image-path", required=True)

    capture_time_parser = subparsers.add_parser("get-capture-time")
    capture_time_parser.add_argument("--photo-id", required=True)

    capture_location_parser = subparsers.add_parser("get-capture-location")
    capture_location_parser.add_argument("--photo-id", required=True)

    remove_entry_parser = subparsers.add_parser("remove-entry")
    remove_entry_parser.add_argument("--date", required=True)
    remove_entry_parser.add_argument("--photo-id", required=True)

    add_entry_parser = subparsers.add_parser("add-entry")
    add_entry_parser.add_argument("--date", required=True)
    add_entry_parser.add_argument("--entry-json")
    add_entry_parser.add_argument("--entry-file")

    args = parser.parse_args()

    if args.command == "prepare-date":
        target = _parse_date(args.date)
        _print_json(prepare_memory_entry_for_date(target.month, target.day, top_n=args.top_n))
        return

    if args.command == "get-daily-payload":
        now: Optional[datetime] = _parse_date(args.date) if args.date else None
        _print_json(get_daily_memory_payload(now=now))
        return

    if args.command == "export-photo":
        _print_json({"photo_id": args.photo_id, "image_path": export_memory_candidate(args.photo_id)})
        return

    if args.command == "cleanup-image":
        cleanup_daily_memory_image(args.image_path)
        _print_json({"status": "ok", "image_path": args.image_path})
        return

    if args.command == "get-capture-time":
        _print_json({"photo_id": args.photo_id, "capture_time": get_memory_capture_time(args.photo_id)})
        return

    if args.command == "get-capture-location":
        _print_json({"photo_id": args.photo_id, "capture_location": get_memory_capture_location(args.photo_id)})
        return

    if args.command == "remove-entry":
        target = _parse_date(args.date)
        removed = remove_memory_library_entry(target.month, target.day, args.photo_id)
        _print_json({
            "status": "removed" if removed else "not_found",
            "date_key": f"{target.month:02d}-{target.day:02d}",
            "photo_id": args.photo_id,
        })
        return

    if args.command == "add-entry":
        target = _parse_date(args.date)
        entry = _load_entry(args)
        add_memory_library_entry(target.month, target.day, entry)
        _print_json({
            "status": "added",
            "date_key": f"{target.month:02d}-{target.day:02d}",
            "photo_id": entry.get("photo_id"),
        })
        return


if __name__ == "__main__":
    main()
