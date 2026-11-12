"""Take the README screenshots and the demo GIF. Starts its own haussim.

    python tools/screenshot.py docs

Needs Playwright and Pillow (pip install playwright pillow).
"""

import io
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
PORT = 8094
URL = f"http://localhost:{PORT}/"
GREY_TEXT = ["--disable-lcd-text"]  # no coloured subpixel fringes on small grey labels
FRAME_MS = 200
WIDTH = 960
SIGNAL = ["#2fcbea", "#ff6b6b", "#f0b23c"]  # live cyan, fault red, amber (dark theme)
CLIP = {"x": 0, "y": 0, "width": 1440, "height": 640}  # header, plant graphic and faceplate top


def launch(p):
    try:
        return p.chromium.launch(headless=True, args=GREY_TEXT)
    except Exception:  # no bundled Chromium; Windows always has Edge
        return p.chromium.launch(headless=True, channel="msedge", args=GREY_TEXT)


def click(page, selector):
    page.locator(selector).dispatch_event("click")  # no scrolling out of the clip


def save_gif(frames, out: Path) -> None:
    sample = frames[::10]
    sheet = Image.new("RGB", (WIDTH, sum(f.height for f in sample)))
    for i, f in enumerate(sample):
        sheet.paste(f, (0, i * f.height))
    palette = sheet.quantize(colors=64 - len(SIGNAL), method=Image.Quantize.MEDIANCUT)
    # Lamps are too small to win a palette slot, so the signal colours go in by hand.
    colours = palette.getpalette()[: (64 - len(SIGNAL)) * 3]
    for hex_colour in SIGNAL:
        colours += [int(hex_colour[i:i + 2], 16) for i in (1, 3, 5)]
    palette = Image.new("P", (1, 1))
    palette.putpalette(colours)
    gif = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    gif[0].save(out, save_all=True, append_images=gif[1:], duration=FRAME_MS, loop=0, optimize=True)
    print(f"{out}: {len(frames)} frames, {out.stat().st_size // 1024} KB")


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    server = subprocess.Popen(
        [sys.executable, "-m", "haussim.cli", "run", "--no-browser", "--speed", "600", "--http-port", str(PORT)],
        cwd=ROOT / "src",
    )
    try:
        time.sleep(2)
        with sync_playwright() as p:
            browser = launch(p)
            errors = []
            page = browser.new_page(viewport={"width": 1440, "height": 900}, color_scheme="dark")
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(URL)
            page.wait_for_timeout(20000)  # about three plant hours of trend
            page.screenshot(path=out / "hmi.png", full_page=True)

            frames: list[Image.Image] = []

            def record(seconds: float) -> None:
                for _ in range(int(seconds * 1000 / FRAME_MS)):
                    img = Image.open(io.BytesIO(page.screenshot(clip=CLIP))).convert("RGB")
                    frames.append(img.resize((WIDTH, round(WIDTH * CLIP["height"] / CLIP["width"])), Image.LANCZOS))
                    page.wait_for_timeout(FRAME_MS)

            record(3)  # heating
            click(page, "#btn-evu")
            record(5)  # grid lock: compressor stops, buffer cools
            click(page, "#btn-evu")
            click(page, "[data-fault=hp]")
            record(6)  # compressor does not start: fault latches, alarm flashes
            click(page, "[data-fault=hp]")
            click(page, "#btn-reset")
            click(page, "#btn-ack")
            record(4)
            save_gif(frames, out / "demo.gif")

            click(page, "[data-fault=short]")  # first, while Q1 still feeds F2
            page.wait_for_timeout(1500)
            click(page, "[data-fault=insulation]")
            page.wait_for_timeout(1500)
            page.locator(".board").screenshot(path=out / "board.png")
            for fault in ("insulation", "short"):
                click(page, f"[data-fault={fault}]")
            for device in ("F2", "Q1"):
                click(page, f'[data-device="{device}"]')
            click(page, "#btn-reset")
            click(page, "#btn-ack")

            page.click("[data-lang=en]")
            click(page, "[data-fault=circ]")
            page.wait_for_timeout(2500)
            page.screenshot(path=out / "hmi-fault.png", full_page=True)
            click(page, "[data-fault=circ]")
            click(page, "#btn-reset")

            light = browser.new_page(viewport={"width": 1440, "height": 900}, color_scheme="light")
            light.goto(URL)
            light.wait_for_timeout(2500)
            light.screenshot(path=out / "hmi-light.png", full_page=True)

            phone = browser.new_page(viewport={"width": 390, "height": 844}, color_scheme="dark", device_scale_factor=2)
            phone.goto(URL)
            phone.wait_for_timeout(2500)
            phone.screenshot(path=out / "hmi-mobile.png")
            browser.close()
            if errors:
                raise SystemExit(f"Page errors: {errors}")
    finally:
        server.terminate()


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "docs"))
