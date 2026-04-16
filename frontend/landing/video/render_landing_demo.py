#!/usr/bin/env python3
"""
Renders 1920x1080 segment frames and calls ffmpeg (no drawtext required).
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BG = (8, 8, 16)
ACCENT = (200, 169, 126)
ACCENT2 = (232, 201, 158)
TEXT2 = (155, 151, 168)
TEXT = (240, 237, 232)
PURPLE = (139, 127, 212)

W, H = 1920, 1080

FONT_SERIF = "/System/Library/Fonts/Supplemental/Georgia.ttf"
FONT_SANS = "/System/Library/Fonts/Supplemental/Arial.ttf"


def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def solid_frame(lines: list[tuple[str, tuple[int, int, int], int]]) -> Image.Image:
    im = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(im)
    fonts = [load_font(FONT_SERIF if size >= 40 else FONT_SANS, size) for _, _, size in lines]
    heights: list[int] = []
    for (text, _, _), font in zip(lines, fonts):
        bbox = draw.textbbox((0, 0), text, font=font)
        heights.append(bbox[3] - bbox[1])
    gap = 22
    total_h = sum(heights) + gap * (len(lines) - 1)
    y = (H - total_h) // 2
    for (text, color, _), font in zip(lines, fonts):
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (W - tw) // 2
        draw.text((x, y), text, fill=color, font=font)
        y += th + gap
    return im


def image_frame(
    src: Path,
    top: str,
    bottom: str | None = None,
    top_size: int = 34,
) -> Image.Image:
    im = Image.new("RGB", (W, H), BG)
    shot = Image.open(src).convert("RGB")
    sw, sh = shot.size
    scale = min((W - 120) / sw, (H - 220) / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    shot = shot.resize((nw, nh), Image.Resampling.LANCZOS)
    x0 = (W - nw) // 2
    y0 = 100 + (H - 100 - nh) // 2
    im.paste(shot, (x0, y0))
    draw = ImageDraw.Draw(im)
    f_top = load_font(FONT_SANS, top_size)
    bbox = draw.textbbox((0, 0), top, font=f_top)
    tw = bbox[2] - bbox[0]
    # semi-transparent bar
    pad = 16
    bar_y = 48
    draw.rectangle(
        (W // 2 - tw // 2 - pad, bar_y - 8, W // 2 + tw // 2 + pad, bar_y + (bbox[3] - bbox[1]) + 8),
        fill=(22, 22, 38),
    )
    draw.text((W // 2 - tw // 2, bar_y), top, fill=ACCENT2, font=f_top)
    if bottom:
        f_b = load_font(FONT_SANS, 26)
        bb = draw.textbbox((0, 0), bottom, font=f_b)
        bw = bb[2] - bb[0]
        draw.text((W // 2 - bw // 2, H - 72), bottom, fill=TEXT2, font=f_b)
    return im


def png_to_mp4(png: Path, out: Path, seconds: float, ffmpeg: str) -> None:
    cmd = [
        ffmpeg,
        "-y",
        "-loop",
        "1",
        "-i",
        str(png),
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=44100:cl=stereo",
        "-t",
        str(seconds),
        "-vf",
        "format=yuv420p",
        "-c:v",
        "libx264",
        "-crf",
        "23",
        "-preset",
        "medium",
        "-c:a",
        "aac",
        "-b:a",
        "96k",
        "-shortest",
        str(out),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def concat_segments(files: list[Path], out: Path, tmp_dir: Path, ffmpeg: str) -> None:
    lst = tmp_dir / "concat_list.txt"
    with open(lst, "w", encoding="utf-8") as f:
        for p in files:
            f.write(f"file '{p.as_posix()}'\n")
    subprocess.run(
        [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)],
        check=True,
    )


def main() -> int:
    root = Path(__file__).resolve().parent
    img_dir = root.parent / "images"
    out_mp4 = root / "demo.mp4"
    ffmpeg = "ffmpeg"

    tmp = Path(tempfile.mkdtemp(prefix="memorial-demo-"))
    try:
        segs: list[Path] = []

        # 1 Hook 10s
        fr = solid_frame(
            [
                ("Photos remember the moment.", ACCENT2, 52),
                ("Stories remember them.", ACCENT, 40),
            ]
        )
        p = tmp / "seg01.png"
        fr.save(p)
        s = tmp / "seg01.mp4"
        png_to_mp4(p, s, 10.0, ffmpeg)
        segs.append(s)

        # 2 Promise 10s
        fr = solid_frame(
            [
                ("Their voice. Their stories. Your family", ACCENT2, 42),
                ("in one place.", TEXT2, 36),
            ]
        )
        p = tmp / "seg02.png"
        fr.save(p)
        s = tmp / "seg02.mp4"
        png_to_mp4(p, s, 10.0, ffmpeg)
        segs.append(s)

        # 3 Timeline 18s
        fr = image_frame(
            img_dir / "feat-timeline.png",
            "Life timeline — dated memories in order",
        )
        p = tmp / "seg03.png"
        fr.save(p)
        s = tmp / "seg03.mp4"
        png_to_mp4(p, s, 18.0, ffmpeg)
        segs.append(s)

        # 4 Chat 17s
        fr = image_frame(
            img_dir / "feat-chat.png",
            "What made you happiest in life?",
            "Answers come from memories you add — see Sources.",
        )
        p = tmp / "seg04.png"
        fr.save(p)
        s = tmp / "seg04.mp4"
        png_to_mp4(p, s, 17.0, ffmpeg)
        segs.append(s)

        # 5 Tree 17s
        fr = image_frame(
            img_dir / "feat-tree.png",
            "Family tree — generations in one map",
        )
        p = tmp / "seg05.png"
        fr.save(p)
        s = tmp / "seg05.mp4"
        png_to_mp4(p, s, 17.0, ffmpeg)
        segs.append(s)

        # 6 CTA 13s
        fr = solid_frame(
            [
                ("Talk to them again.", ACCENT2, 56),
                ("Create a memorial — start free", TEXT, 38),
                ("/app/register", PURPLE, 30),
            ]
        )
        p = tmp / "seg06.png"
        fr.save(p)
        s = tmp / "seg06.mp4"
        png_to_mp4(p, s, 13.0, ffmpeg)
        segs.append(s)

        concat_segments(segs, out_mp4, tmp, ffmpeg)
        print(f"Wrote {out_mp4} ({out_mp4.stat().st_size // 1024} KB)")
    finally:
        for child in tmp.iterdir():
            child.unlink(missing_ok=True)
        tmp.rmdir()

    return 0


if __name__ == "__main__":
    sys.exit(main())
