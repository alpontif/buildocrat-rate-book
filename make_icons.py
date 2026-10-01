"""Generate the app icons for the installable site (run once; icons are committed)."""
from PIL import Image, ImageDraw, ImageFont
import os

GREEN = (214, 240, 74)
WHITE = (21, 21, 21)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "icons")
os.makedirs(OUT, exist_ok=True)

def icon(size, safe=1.0, rounded=True):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = int(size * 0.18) if rounded else 0
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=GREEN)
    inner = size * safe
    f = ImageFont.truetype(FONT, int(inner * 0.62))
    box = d.textbbox((0, 0), "B", font=f)
    w, h = box[2] - box[0], box[3] - box[1]
    x = (size - w) / 2 - box[0]
    y = (size - h) / 2 - box[1] - inner * 0.04
    d.text((x, y), "B", font=f, fill=WHITE)
    # ledger rule under the letter: the price-book line
    lw = inner * 0.44; ly = (size + h) / 2 + inner * 0.04
    d.rectangle([(size - lw) / 2, ly, (size + lw) / 2, ly + max(2, inner * 0.035)], fill=WHITE)
    return img

icon(192).save(os.path.join(OUT, "icon-192.png"))
icon(512).save(os.path.join(OUT, "icon-512.png"))
icon(512, safe=0.72, rounded=False).save(os.path.join(OUT, "icon-maskable-512.png"))
icon(180, rounded=False).convert("RGB").save(os.path.join(OUT, "apple-touch-icon.png"))
print("icons written to", OUT)
