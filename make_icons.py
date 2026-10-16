"""Generate the app icons for the installable site (run once; icons are committed)."""
from PIL import Image, ImageDraw, ImageFont
import os

GREEN = (214, 240, 74)
WHITE = (21, 21, 21)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "icons")
os.makedirs(OUT, exist_ok=True)

def icon(size, safe=1.0, rounded=True):
    GREENF = (0, 166, 81); MINT = (205, 235, 216)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = int(size * 0.2) if rounded else 0
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=GREENF)
    inner = size * safe
    hs = [0.45, 0.8, 0.55, 1.0, 0.35, 0.7, 0.5, 0.9]
    bw = inner * 0.05; gap = inner * 0.03; H = inner * 0.46
    total = len(hs) * bw + (len(hs) - 1) * gap
    x = (size - total) / 2; base = size / 2 + H / 2
    for i, h in enumerate(hs):
        d.rounded_rectangle([x, base - H * h, x + bw, base], radius=max(1, bw * 0.3), fill=(255, 255, 255) if i % 3 else MINT)
        x += bw + gap
    return img

icon(192).save(os.path.join(OUT, "icon-192.png"))
icon(512).save(os.path.join(OUT, "icon-512.png"))
icon(512, safe=0.72, rounded=False).save(os.path.join(OUT, "icon-maskable-512.png"))
icon(180, rounded=False).convert("RGB").save(os.path.join(OUT, "apple-touch-icon.png"))
print("icons written to", OUT)
