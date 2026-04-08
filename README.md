# memory-day

![Platform](https://img.shields.io/badge/platform-macOS-black)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Status](https://img.shields.io/badge/status-initial_public_skeleton-orange)

Build “On This Day” memory payloads from your local macOS Photos library.

> Uses Photos.app, Photos.sqlite, AppleScript, and `sips`.

## What this project is

`memory-day` is a small macOS-only engine for building “On This Day” memory payloads from your local Photos.app library.

It focuses on:

- discovering historical photos by month and day
- exporting temporary photo copies
- reading capture time
- reading capture location
- maintaining a local memory library
- exposing CLI entrypoints for maintenance workflows

It does **not** include:

- push delivery integrations
- scheduling logic
- weather triggers
- private `config.py`
- real personal `memory_library.json` data

## Delivery integrations

This project does not ship with any built-in delivery channel.

It focuses on generating local “On This Day” memory payloads only.
You can connect the generated payload to your own delivery system, such as Feishu, WeCom, DingTalk, Telegram, email, or a custom webhook.

In other words, the repository is intentionally delivery-agnostic: you are free to choose the messaging or notification channel that fits your workflow.

### How to integrate your own channel

The easiest way is to keep `memory-day` responsible for payload generation only, and add a thin delivery adapter in your own project.

A typical integration flow looks like this:

1. call `memory_day.service.get_daily_memory_payload()`
2. read `title`, `text`, and `image_path` from the returned payload
3. upload or attach the local image if your channel supports images
4. send the message through your own provider

Different channels require different configuration. Some only need a webhook URL, while others may require app credentials, bot tokens, chat IDs, SMTP settings, or media upload steps.

For that reason, this repository does not try to standardize delivery configuration into a single universal API key. In most cases, it is better to choose one channel that fits your workflow and wire it up in your own script or application layer.

If you want the lowest-friction starting point, begin with a simple webhook-based integration or a Feishu bot integration first.

## Platform constraints

This project is **macOS-only** and depends on:

- Photos.app
- Photos.sqlite
- AppleScript (`osascript`)
- `sips`

If you are not on macOS, or you do not have a local Photos library, this project will not work as-is.

## Project structure

```text
memory-day/
├── memory_day/
│   ├── __init__.py
│   ├── service.py
│   ├── photos.py
│   ├── library.py
│   └── cli.py
├── content/
│   └── memory_library.example.json
├── config.example.py
├── .gitignore
├── LICENSE
├── requirements.txt
├── RELEASE_CHECKLIST.md
└── README.md
```

## Quick start

### 1. Prepare local config

Copy the example config:

```bash
cp config.example.py config.py
```

Then update the values for your local environment:

- `MEMORY_LIBRARY_PATH`
- `MEMORY_EXPORT_DIR`
- `PHOTOS_DB_PATH`

### 2. Prepare a local memory library

Do not commit a real `content/memory_library.json`.

For first-time local use:

```bash
cp content/memory_library.example.json content/memory_library.json
```

This skeleton intentionally does **not** include a real `config.py` or `content/memory_library.json`. Create them locally when you want to run the project.

### 3. Basic verification

```bash
python3 -m py_compile memory_day/__init__.py memory_day/service.py memory_day/photos.py memory_day/library.py memory_day/cli.py
```

## Configuration

The current version reads configuration from a root-level `config.py`.

At minimum, you need these path settings:

```python
from pathlib import Path

BASE_DIR = Path(__file__).parent
MEMORY_LIBRARY_PATH = BASE_DIR / "content" / "memory_library.json"
MEMORY_EXPORT_DIR = Path("/tmp/memory-day-exports")
PHOTOS_DB_PATH = Path.home() / "Pictures" / "Photos Library.photoslibrary" / "database" / "Photos.sqlite"
```

## CLI usage

```bash
python3 -m memory_day.cli prepare-date --date 2026-04-07 --top-n 4
python3 -m memory_day.cli get-daily-payload --date 2026-04-07
python3 -m memory_day.cli export-photo --photo-id <photo_id>
python3 -m memory_day.cli cleanup-image --image-path <image_path>
python3 -m memory_day.cli get-capture-time --photo-id <photo_id>
python3 -m memory_day.cli get-capture-location --photo-id <photo_id>
python3 -m memory_day.cli add-entry --date 2026-04-07 --entry-json '{"photo_id":"...","filename":"...","year":2020,"description":"...","title":"...","text":"..."}'
```

## Example memory library format

`content/memory_library.json` is organized by `MM-DD` keys:

```json
{
  "04-07": [
    {
      "photo_id": "EXAMPLE-PHOTO-ID-001",
      "filename": "example-photo.jpg",
      "year": 2018,
      "description": "A person standing in front of a large window with a blue-sky silhouette.",
      "title": "On this day 8 years ago",
      "text": "On this day in 2018, you stood in front of a huge window...",
      "capture_time": "2018-04-07 22:31",
      "capture_location": "Example City - Example Place"
    }
  ]
}
```

Required fields:

- `photo_id`
- `filename`
- `year`
- `description`
- `title`
- `text`

Optional fields:

- `capture_time`
- `capture_location`

## Privacy and safety

Do not commit the following:

- real `config.py`
- `content/memory_library.json`
- exported personal photos
- local logs
- local state files

Before publishing, run through `RELEASE_CHECKLIST.md`.

## License

MIT
