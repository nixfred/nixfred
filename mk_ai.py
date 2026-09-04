"""Build 'A I' and a multiplication sign in Omarchy's own letterform grammar.

Grammar reverse-engineered from /usr/share/omarchy/logo.svg:
  - everything sits on a 15-unit grid
  - stems are 45 units (3 cells) wide
  - cap height is 240 units (y 15..255)
  - every letter carries a 2-step chamfer on its TOP-LEFT and BOTTOM-RIGHT corner
    (verified on O, M, A, R, C, H, Y)
The 'A' is lifted verbatim from the logo. The 'I' is constructed from the rule
above -- the logo has no I. The multiplication sign is a pixel X on the same
grid with 45-unit strokes so it carries the same weight as the letters.
"""
import json

G = 15.0          # grid unit
STEM = 45.0       # stem width (3 cells)
TOP, BOT = 15.0, 255.0
CAP = BOT - TOP   # 240

def letter_I(w=75.0):
    """A stem with the font's top-left and bottom-right 2-step chamfers."""
    c = 2 * G  # chamfer run = 30
    return (f"M{c},{TOP} H{w} V{BOT-c} H{w-G} V{BOT-G} H{w-c} V{BOT} "
            f"H0 V{TOP+c} H{G} V{TOP+G} H{c} Z")

def pixel_x(cells=10, thick=3):
    """Pixel X on the 15-grid, `thick` cells wide (3 cells = 45 = stem width)."""
    half = (thick - 1) / 2.0
    rects = []
    for r in range(cells):
        for c in range(cells):
            on_main = abs(r - c) <= half
            on_anti = abs(r + c - (cells - 1)) <= half
            if on_main or on_anti:
                rects.append(f"M{c*G},{r*G} h{G} v{G} h-{G} Z")
    return " ".join(rects)

if __name__ == "__main__":
    L = json.load(open('logo_svg.json'))
    A = L['paths'][3]          # the real A, bbox x 405..555
    out = {
        "A":   {"d": A["d"], "fr": A["fr"], "x0": 405.0, "w": 150.0},
        "I":   {"d": letter_I(75.0), "fr": None, "x0": 0.0, "w": 75.0},
        "X":   {"d": pixel_x(10, 3), "fr": None, "x0": 0.0, "w": 150.0, "h": 150.0},
    }
    json.dump(out, open('ai_glyphs.json', 'w'))

    # proof sheet: real letters beside the constructed ones
    o = ['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="330" viewBox="0 0 1100 330">',
         '<rect width="1100" height="330" fill="#0a0d16"/>']
    x = 30
    # real H for comparison
    H = L['paths'][5]
    o.append(f'<g transform="translate({x-885} 20)" fill="#4d5f85"><path d="{H["d"]}"/></g>'); x += 220
    o.append(f'<g transform="translate({x-405} 20)" fill="#e6edf7"><path d="{A["d"]}" fill-rule="evenodd" clip-rule="evenodd"/></g>'); x += 190
    o.append(f'<g transform="translate({x} 20)" fill="#e6edf7"><path d="{out["I"]["d"]}"/></g>'); x += 120
    o.append(f'<g transform="translate({x} {20+ (CAP-150)/2 + TOP})" fill="#7dd3fc"><path d="{out["X"]["d"]}"/></g>')
    o.append('</svg>')
    open('proof.svg', 'w').write("\n".join(o))
    print("wrote ai_glyphs.json + proof.svg")
