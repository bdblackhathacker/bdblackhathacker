#!/usr/bin/env python3
"""Custom contribution snake for bdblackhathacker. No third-party service.

Fetches the public contributions calendar, rebuilds the grid in gray-hacker
colors and overlays an animated serpentine snake (SMIL - works in READMEs).
Output: assets/snake-dark.svg (committed to the repo, always renders).

Run:  python3 snake/generate.py
Auto: .github/workflows/snake.yml runs this weekly + on every push to main.
"""
import datetime
import re
import sys
import urllib.request

USER = "bdblackhathacker"
OUT = "assets/snake-dark.svg"

CELL, GAP, PAD = 10, 3, 14
PITCH = CELL + GAP
COLORS = {
    "0": "#161b22",
    "1": "#0e4429",
    "2": "#006d32",
    "3": "#26a641",
    "4": "#00ff41",  # custom max: brighter than GitHub default
}
BG, BORDER, TEXT = "#0d1117", "#30363d", "#8b949e"
SNAKE = "#00ff41"


def fetch_days():
    url = f"https://github.com/users/{USER}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "custom-snake/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8", "replace")
    # current GitHub markup: <td ... data-date="YYYY-MM-DD" ... data-level="N"
    #   class="ContributionCalendar-day"> (+ tooltip holds the count)
    tds = re.findall(r"<td[^>]*data-date=[^>]*>", html)
    tips = re.findall(r"<tool-tip[^>]*>(.*?)</tool-tip>", html, re.S)
    if not tds:
        sys.exit("ERROR: no contribution cells parsed")
    days = []
    for i, tag in enumerate(tds):
        date = re.search(r'data-date="([^"]+)"', tag)
        level = re.search(r'data-level="([^"]+)"', tag)
        if not (date and level):
            continue
        count = 0
        if i < len(tips):
            m = re.search(r"(\d[\d,]*)\s+contribution", tips[i])
            if m:
                count = int(m.group(1).replace(",", ""))
        d = datetime.date.fromisoformat(date.group(1))
        days.append((d, count, level.group(1)))
    if not days:
        sys.exit("ERROR: no contribution rects parsed")
    return days


def main():
    days = fetch_days()
    first = days[0][0]
    start = first - datetime.timedelta(days=(first.weekday() + 1) % 7)  # prev Sunday
    cells = {}  # (col,row) -> level
    for d, _count, level in days:
        i = (d - start).days
        cells[(i // 7, i % 7)] = level
    cols = max(c for c, _ in cells) + 1

    def cx(c):
        return PAD + c * PITCH + CELL / 2

    def cy(r):
        return PAD + 18 + r * PITCH + CELL / 2  # 18px for label

    # serpentine path: row 0 L->R, row 1 R->L, ...
    pts = []
    for r in range(7):
        order = range(cols) if r % 2 == 0 else range(cols - 1, -1, -1)
        pts += [(cx(c), cy(r)) for c in order]
    d_path = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)

    w = PAD * 2 + cols * PITCH - GAP
    h = PAD * 2 + 18 + 7 * PITCH - GAP

    rects = []
    for c in range(cols):
        for r in range(7):
            level = cells.get((c, r), "0")
            x = PAD + c * PITCH
            y = PAD + 18 + r * PITCH
            rects.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" '
                f'fill="{COLORS.get(level, COLORS["0"])}"/>'
            )

    total = len(days)
    year_total = sum(n for _, n, _ in days)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="monospace">
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="6" fill="{BG}" stroke="{BORDER}"/>
<text x="{PAD}" y="{PAD + 2}" font-size="11" fill="{SNAKE}">root@bdblackhathacker:~/snake$ ./eat_contributions --all</text>
{chr(10).join(rects)}
<path d="{d_path}" fill="none" stroke="{SNAKE}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" opacity="0.22"/>
<path d="{d_path}" fill="none" stroke="{SNAKE}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="7 6" opacity="0.9">
<animate attributeName="stroke-dashoffset" from="260" to="0" dur="6s" repeatCount="indefinite"/>
</path>
<g>
<animateMotion dur="18s" repeatCount="indefinite" path="{d_path}"/>
<circle r="6.5" fill="{SNAKE}" opacity="0.30"/>
<circle r="3.4" fill="{SNAKE}"/>
</g>
<text x="{w - PAD}" y="{h - 6}" font-size="10" fill="{TEXT}" text-anchor="end">{year_total} contributions / {total} days // custom-built, zero deps</text>
</svg>
"""
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"OK: {OUT} ({w}x{h}, {cols} weeks, {year_total} contributions)")


if __name__ == "__main__":
    main()
