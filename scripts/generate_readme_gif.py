from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT / "docs" / "images"
HOME = IMAGE_DIR / "metaagent-home.png"
CHAT = IMAGE_DIR / "metaagent-chat.png"
OUTPUT = IMAGE_DIR / "metaagent-demo.gif"

MAX_WIDTH = 1120
FRAME_MS = 90


def main() -> None:
    home = load_frame(HOME)
    chat = load_frame(CHAT)
    frames: list[Image.Image] = []

    frames.extend([home] * 10)
    for index in range(14):
        ratio = index / 13
        frames.append(Image.blend(home, chat, ratio))
    frames.extend([annotate(chat, pulse=index) for index in range(18)])
    frames.extend([chat] * 10)

    frames[0].save(
        OUTPUT,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_MS,
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


def load_frame(path: Path) -> Image.Image:
    with Image.open(path) as image:
        image = image.convert("RGB")
        if image.width > MAX_WIDTH:
            scale = MAX_WIDTH / image.width
            height = int(image.height * scale)
            image = image.resize((MAX_WIDTH, height), Image.Resampling.LANCZOS)
        return image


def annotate(frame: Image.Image, pulse: int) -> Image.Image:
    image = frame.copy()
    draw = ImageDraw.Draw(image)
    width, height = image.size
    scale = width / 1120

    # Pulse the active agent and worker response areas to make the GIF read as a workflow.
    alpha = 1 - abs((pulse % 9) - 4) / 4
    color = (37, 99, 235)
    line_width = max(2, int(3 * scale))
    margin = int((6 + alpha * 8) * scale)

    agent_box = scaled_box((12, 145, 180, 176), scale, margin)
    response_box = scaled_box((265, 132, 830, 184), scale, margin)
    draw.rounded_rectangle(agent_box, radius=int(10 * scale), outline=color, width=line_width)
    draw.rounded_rectangle(response_box, radius=int(10 * scale), outline=color, width=line_width)

    # Add a small progress marker in the lower-right corner without covering the UI.
    dot_radius = int(4 * scale)
    start_x = width - int(80 * scale)
    y = height - int(30 * scale)
    for idx in range(3):
        fill = color if idx <= pulse % 3 else (203, 213, 225)
        x = start_x + idx * int(18 * scale)
        draw.ellipse((x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius), fill=fill)
    return image


def scaled_box(box: tuple[int, int, int, int], scale: float, margin: int) -> tuple[int, int, int, int]:
    left, top, right, bottom = [int(value * scale) for value in box]
    return left - margin, top - margin, right + margin, bottom + margin


if __name__ == "__main__":
    main()
