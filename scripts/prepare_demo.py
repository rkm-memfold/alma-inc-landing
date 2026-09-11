#!/usr/bin/env python3
"""Turn a screen recording into the web-ready demo the landing page plays.

The desktop on the homepage opens `/page/desktop/demos/<name>.mp4` on a wide
screen, `<name>-sm.mp4` on a phone, and shows `<name>-poster.jpg` until one of
them plays. Screen recordings come off a Mac as multi-hundred-megabyte 4K
movies, which is far too heavy to serve, so this trims and re-encodes them with
`avconvert` — part of macOS, so nothing has to be installed.

    python3 scripts/prepare_demo.py blender ~/Desktop/rocket.mov \\
        --start 12 --duration 48

Names are limited to the demos the page knows about. Pass --keep-poster to
re-encode the videos without touching an existing poster, and --no-small to
skip the phone-sized copy.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEMOS = ROOT / "public" / "page" / "desktop" / "demos"
KNOWN = ("blender", "paint")

# avconvert preset -> the longest edge it produces. 720p is the sweet spot for a
# screen recording in a window this size; 1080p roughly triples the file.
PRESETS = {
    "360p": "Preset640x480",
    "540p": "Preset960x540",
    "720p": "Preset1280x720",
    "1080p": "Preset1920x1080",
}


def run(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(
            f"{command[0]} failed ({result.returncode}):\n"
            f"{result.stderr.strip() or result.stdout.strip()}"
        )


def transcode(source: Path, destination: Path, preset: str, start: float, duration: float | None) -> None:
    command = [
        "/usr/bin/avconvert",
        "--source", str(source),
        "--output", str(destination),
        "--preset", PRESETS[preset],
        "--replace",
        "--progress",
    ]
    if start:
        command += ["--start", str(start)]
    if duration:
        command += ["--duration", str(duration)]
    run(command)


def make_poster(video: Path, destination: Path) -> bool:
    """Ask QuickLook for the movie's poster frame and save it as a JPEG."""
    with tempfile.TemporaryDirectory() as scratch:
        run(["/usr/bin/qlmanage", "-t", "-s", "1280", "-o", scratch, str(video)])
        rendered = list(Path(scratch).glob("*.png"))
        if not rendered:
            return False
        run([
            "/usr/bin/sips",
            "-s", "format", "jpeg",
            "-s", "formatOptions", "82",
            str(rendered[0]),
            "--out", str(destination),
        ])
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("name", choices=KNOWN, help="which demo this recording is")
    parser.add_argument("source", type=Path, help="the original screen recording")
    parser.add_argument("--start", type=float, default=0.0, help="seconds to skip from the beginning")
    parser.add_argument("--duration", type=float, default=None, help="seconds to keep (default: to the end)")
    parser.add_argument("--preset", choices=sorted(PRESETS), default="720p")
    parser.add_argument("--keep-poster", action="store_true", help="leave the existing poster alone")
    parser.add_argument("--no-small", action="store_true", help="skip the phone-sized copy")
    arguments = parser.parse_args()

    source = arguments.source.expanduser()
    if not source.is_file():
        sys.exit(f"no such recording: {source}")

    DEMOS.mkdir(parents=True, exist_ok=True)
    video = DEMOS / f"{arguments.name}.mp4"
    poster = DEMOS / f"{arguments.name}-poster.jpg"

    with tempfile.TemporaryDirectory() as scratch:
        staged = Path(scratch) / f"{arguments.name}.mp4"
        transcode(source, staged, arguments.preset, arguments.start, arguments.duration)
        shutil.move(str(staged), video)

    megabytes = video.stat().st_size / (1024 * 1024)
    print(f"wrote {video.relative_to(ROOT)} ({megabytes:.1f} MB)")
    if megabytes > 12:
        print(
            "  note: over 12 MB. Trim harder with --start/--duration, or drop to "
            "--preset 540p, so the page stays quick even on a wide screen."
        )

    if not arguments.no_small:
        small = DEMOS / f"{arguments.name}-sm.mp4"
        with tempfile.TemporaryDirectory() as scratch:
            staged = Path(scratch) / f"{arguments.name}-sm.mp4"
            transcode(source, staged, "360p", arguments.start, arguments.duration)
            shutil.move(str(staged), small)
        print(f"wrote {small.relative_to(ROOT)} ({small.stat().st_size / (1024 * 1024):.1f} MB)")

    if arguments.keep_poster:
        return
    if make_poster(video, poster):
        print(f"wrote {poster.relative_to(ROOT)}")
    else:
        print(f"could not render a poster; {poster.relative_to(ROOT)} was left as it was")


if __name__ == "__main__":
    main()
