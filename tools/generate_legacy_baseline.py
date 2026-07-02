#!/usr/bin/env python3
"""Generate reproducible baseline outputs from the legacy Python engine."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import warnings
from pathlib import Path
from typing import Any, Dict, List

from PIL import Image, ImageDraw

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
warnings.filterwarnings("ignore", category=RuntimeWarning, module=r"sklearn\..*")
warnings.filterwarnings(
    "ignore",
    message=r"Could not find the number of physical cores.*",
    module=r"joblib\..*",
)

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import main as legacy_backend  # noqa: E402

FIXTURE_DIR = ROOT / "tests" / "fixtures" / "baseline"
REFERENCE_DIR = ROOT / "tests" / "baseline" / "reference"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_shapes_fixture(path: Path) -> None:
    image = Image.new("RGB", (128, 96), "#ffffff")
    draw = ImageDraw.Draw(image)

    draw.rectangle((8, 8, 58, 52), fill="#e63946")
    draw.ellipse((68, 10, 120, 62), fill="#457b9d")
    draw.polygon([(18, 78), (50, 58), (82, 84), (44, 90)], fill="#f4a261")
    draw.line((6, 88, 122, 70), fill="#111111", width=5)
    draw.rectangle((88, 68, 118, 90), fill="#2a9d8f")
    image.save(path)


def write_poster_fixture(path: Path) -> None:
    width, height = 112, 88
    image = Image.new("RGB", (width, height))
    pixels = image.load()

    for y in range(height):
        for x in range(width):
            r = int(40 + 160 * x / (width - 1))
            g = int(30 + 120 * y / (height - 1))
            b = 120 if (x // 14 + y // 11) % 2 == 0 else 190
            pixels[x, y] = (r, g, b)

    draw = ImageDraw.Draw(image)
    draw.ellipse((12, 14, 58, 60), fill="#ffcc00")
    draw.rectangle((66, 18, 100, 70), fill="#1d3557")
    draw.polygon([(20, 76), (52, 58), (92, 80)], fill="#06d6a0")
    image.save(path)


def write_icon_fixture(path: Path) -> None:
    image = Image.new("RGB", (96, 96), "#ffffff")
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle((8, 8, 88, 88), radius=12, fill="#111111")
    draw.rounded_rectangle((14, 14, 82, 82), radius=8, fill="#ffffff")
    draw.pieslice((24, 22, 74, 72), 30, 330, fill="#ffd166")
    draw.rectangle((44, 54, 54, 82), fill="#118ab2")
    draw.polygon([(22, 80), (42, 58), (62, 80)], fill="#06d6a0")
    draw.polygon([(52, 80), (70, 62), (86, 80)], fill="#ef476f")
    image.save(path)


def generate_fixtures() -> List[Dict[str, Any]]:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

    fixtures = [
        {
            "name": "flat_shapes",
            "path": FIXTURE_DIR / "flat_shapes.png",
            "writer": write_shapes_fixture,
        },
        {
            "name": "poster_gradient",
            "path": FIXTURE_DIR / "poster_gradient.png",
            "writer": write_poster_fixture,
        },
        {
            "name": "icon_marks",
            "path": FIXTURE_DIR / "icon_marks.png",
            "writer": write_icon_fixture,
        },
    ]

    result = []
    for fixture in fixtures:
        fixture["writer"](fixture["path"])
        with Image.open(fixture["path"]) as image:
            width, height = image.size
        result.append(
            {
                "name": fixture["name"],
                "path": fixture["path"],
                "width": width,
                "height": height,
                "sha256": sha256_file(fixture["path"]),
            }
        )

    return result


def conversion_cases() -> List[Dict[str, Any]]:
    return [
        {
            "name": "flat_shapes_light_6",
            "fixture": "flat_shapes",
            "colors": 6,
            "smoothing": "light",
            "exclude_white": False,
            "exclude_black": False,
        },
        {
            "name": "flat_shapes_no_white_6",
            "fixture": "flat_shapes",
            "colors": 6,
            "smoothing": "light",
            "exclude_white": True,
            "exclude_black": False,
        },
        {
            "name": "poster_gradient_aggressive_8",
            "fixture": "poster_gradient",
            "colors": 8,
            "smoothing": "aggressive",
            "exclude_white": False,
            "exclude_black": False,
        },
        {
            "name": "icon_marks_no_black_7",
            "fixture": "icon_marks",
            "colors": 7,
            "smoothing": "light",
            "exclude_white": False,
            "exclude_black": True,
        },
    ]


def run_case(case: Dict[str, Any], fixture_lookup: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    fixture = fixture_lookup[case["fixture"]]
    image_bytes = fixture["path"].read_bytes()
    task_id = f"baseline-{case['name']}"

    start = time.perf_counter()
    legacy_backend.process_image_task(
        task_id=task_id,
        image_bytes=image_bytes,
        colors=case["colors"],
        smoothing=case["smoothing"],
        exclude_white=case["exclude_white"],
        exclude_black=case["exclude_black"],
    )
    duration_seconds = time.perf_counter() - start

    task = legacy_backend.tasks[task_id]
    if task["status"] != "completed":
        raise RuntimeError(f"{case['name']} failed: {task.get('message', 'unknown error')}")

    result = task["result"]
    svg = result["svg"]
    palette = result["palette"]

    svg_path = REFERENCE_DIR / f"{case['name']}.svg"
    palette_path = REFERENCE_DIR / f"{case['name']}.palette.json"
    metadata_path = REFERENCE_DIR / f"{case['name']}.metadata.json"

    svg_path.write_text(svg, encoding="utf-8")
    palette_path.write_text(json.dumps(palette, indent=2) + "\n", encoding="utf-8")

    metadata = {
        "case": case,
        "fixture": {
            "name": fixture["name"],
            "path": str(fixture["path"].relative_to(ROOT)),
            "width": fixture["width"],
            "height": fixture["height"],
            "sha256": fixture["sha256"],
        },
        "result": {
            "svg_path": str(svg_path.relative_to(ROOT)),
            "palette_path": str(palette_path.relative_to(ROOT)),
            "svg_sha256": sha256_text(svg),
            "svg_bytes": len(svg.encode("utf-8")),
            "path_count": svg.count("<path "),
            "palette": palette,
            "palette_size": len(palette),
        },
        "runtime": {
            "duration_seconds": round(duration_seconds, 4),
        },
    }

    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def main() -> None:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    fixtures = generate_fixtures()
    fixture_lookup = {fixture["name"]: fixture for fixture in fixtures}

    cases = conversion_cases()
    results = [run_case(case, fixture_lookup) for case in cases]

    manifest = {
        "description": "Legacy Python baseline for RasterSVG migration.",
        "engine": {
            "entrypoint": "backend.main.process_image_task",
            "max_resize_px": 1000,
            "potrace_trace": {
                "turdsize": 4,
                "alphamax": 1,
            },
        },
        "fixtures": [
            {
                "name": fixture["name"],
                "path": str(fixture["path"].relative_to(ROOT)),
                "width": fixture["width"],
                "height": fixture["height"],
                "sha256": fixture["sha256"],
            }
            for fixture in fixtures
        ],
        "cases": [
            {
                "name": item["case"]["name"],
                "fixture": item["case"]["fixture"],
                "colors": item["case"]["colors"],
                "smoothing": item["case"]["smoothing"],
                "exclude_white": item["case"]["exclude_white"],
                "exclude_black": item["case"]["exclude_black"],
                "svg_path": item["result"]["svg_path"],
                "palette_path": item["result"]["palette_path"],
                "metadata_path": str((REFERENCE_DIR / f"{item['case']['name']}.metadata.json").relative_to(ROOT)),
                "svg_sha256": item["result"]["svg_sha256"],
                "svg_bytes": item["result"]["svg_bytes"],
                "path_count": item["result"]["path_count"],
                "palette_size": item["result"]["palette_size"],
                "duration_seconds": item["runtime"]["duration_seconds"],
            }
            for item in results
        ],
    }

    manifest_path = REFERENCE_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Generated {len(fixtures)} fixtures and {len(results)} baseline cases.")
    print(f"Manifest: {manifest_path.relative_to(ROOT)}")
    for item in manifest["cases"]:
        print(
            f"- {item['name']}: {item['svg_bytes']} bytes, "
            f"{item['path_count']} paths, {item['duration_seconds']}s"
        )


if __name__ == "__main__":
    main()
