"""Shared config: tool paths (from ~/.short-edit-kit/config.json, written by setup) and the active brand pack.

Env overrides: SEK_CONFIG (config path), SEK_BRAND (brand name or folder), WHISPER_MODEL, SEK_FFMPEG.
"""
import json
import os
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.expanduser(os.environ.get("SEK_CONFIG", "~/.short-edit-kit/config.json"))
_TOOLS = os.path.expanduser("~/video-tools")

DEFAULTS = {
    "tools_dir": _TOOLS,
    "ffmpeg": os.path.join(_TOOLS, "bin", "ffmpeg"),
    "python": os.path.join(_TOOLS, "venv", "bin", "python"),
    "model": os.path.join(_TOOLS, "models", "large-v3-turbo"),
    "remotion_dir": os.path.join(_TOOLS, "remotion"),
    "brand": "groww",
}


def cfg() -> dict:
    c = dict(DEFAULTS)
    if os.path.exists(CONFIG_PATH):
        c.update(json.load(open(CONFIG_PATH)))
    if os.environ.get("SEK_FFMPEG"):
        c["ffmpeg"] = os.environ["SEK_FFMPEG"]
    if os.environ.get("WHISPER_MODEL"):
        c["model"] = os.environ["WHISPER_MODEL"]
    if os.environ.get("SEK_BRAND"):
        c["brand"] = os.environ["SEK_BRAND"]
    return {k: os.path.expanduser(v) if isinstance(v, str) else v for k, v in c.items()}


def ffmpeg() -> str:
    return cfg()["ffmpeg"]


def brand_dir(name: str = "") -> str:
    """A brand pack is a folder with brand.json + logo/. Name = folder under brands/, or a path."""
    name = name or cfg()["brand"]
    d = os.path.expanduser(name) if os.sep in name else os.path.join(PLUGIN_ROOT, "brands", name)
    if not os.path.exists(os.path.join(d, "brand.json")):
        sys.exit(f"brand pack not found: {d}")
    return d


def brand(name: str = "") -> dict:
    d = brand_dir(name)
    b = json.load(open(os.path.join(d, "brand.json")))
    b["_dir"] = d
    return b


def load(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(obj, path: str, indent=None) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)
