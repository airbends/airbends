#!/usr/bin/env python3
"""
generate_contribution_svg.py
-----------------------------------------------------------------
Fetches YOUR real GitHub contribution calendar via GitHub's GraphQL
API and renders it as an SVG that exactly matches your GitHub
profile graph (same squares, same colors, same totals) — because
it uses the real data and the real colors GitHub itself returns.

USAGE:
    export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx   # PAT, needs "read:user" scope
    export GITHUB_USERNAME=airbends
    python3 generate_contribution_svg.py

Outputs: contribution-graph.svg  (in the current directory)
-----------------------------------------------------------------
"""

import os
import sys
import json
import urllib.request

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "airbends")
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "contribution-graph.svg")

if not GITHUB_TOKEN:
    sys.exit("ERROR: set GITHUB_TOKEN env var (a GitHub personal access token with 'read:user' scope)")

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            color
          }
        }
      }
    }
  }
}
"""

def fetch_contributions(username, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": username}}).encode(),
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "contribution-svg-script",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    if "errors" in data:
        sys.exit(f"GitHub API error: {data['errors']}")
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]

def build_svg(calendar, username):
    weeks = calendar["weeks"]
    total = calendar["totalContributions"]

    CELL, GAP = 12, 3
    PAD_LEFT, PAD_TOP, PAD_BOTTOM = 26, 24, 30
    n_weeks = len(weeks)
    width = PAD_LEFT + n_weeks * (CELL + GAP) + 10
    height = PAD_TOP + 7 * (CELL + GAP) + PAD_BOTTOM

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">'
    )
    parts.append("""<style>
text.lbl{fill:#7d8590;font-size:12px;font-weight:600;}
text.name{fill:#e6edf3;font-size:14px;font-weight:700;}
text.total{fill:#8b949e;font-size:12px;font-weight:500;}
.c{transform-box:fill-box;transform-origin:center;opacity:0;animation:pop .5s ease-out both, flash .6s ease-out both;}
@keyframes pop{0%{opacity:0;transform:scale(.2)}60%{opacity:1;transform:scale(1.1)}100%{opacity:1;transform:scale(1)}}
@keyframes flash{0%{filter:brightness(2.2)}45%{filter:brightness(2.2)}100%{filter:brightness(1)}}
</style>""")
    parts.append(f'<rect width="{width}" height="{height}" rx="10" fill="#0d1117"/>')
    parts.append(f'<text class="name" x="{PAD_LEFT}" y="14">{username}</text>')

    # month labels: mark the first week a new month starts in
    seen_months = set()
    month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    for w_idx, week in enumerate(weeks):
        first_day = week["contributionDays"][0]["date"] if week["contributionDays"] else None
        if first_day:
            month = int(first_day.split("-")[1])
            if month not in seen_months:
                seen_months.add(month)
                x = PAD_LEFT + w_idx * (CELL + GAP)
                parts.append(f'<text class="lbl" x="{x}" y="{PAD_TOP - 8}">{month_names[month-1]}</text>')

    for idx, d in enumerate(["Mon", "Wed", "Fri"]):
        y = PAD_TOP + (idx * 2 + 1) * (CELL + GAP) + 9
        parts.append(f'<text class="lbl" x="0" y="{y}">{d}</text>')

    delay_step = 0.011
    i = 0
    for w_idx, week in enumerate(weeks):
        for d_idx, day in enumerate(week["contributionDays"]):
            x = PAD_LEFT + w_idx * (CELL + GAP)
            y = PAD_TOP + d_idx * (CELL + GAP)
            color = day["color"]           # exact color GitHub itself uses
            delay = i * delay_step
            parts.append(
                f'<rect class="c" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="3" '
                f'fill="{color}" style="animation-delay:{delay:.3f}s"/>'
            )
            i += 1

    parts.append(f'<text class="total" x="{PAD_LEFT}" y="{height - 8}">{total:,} contributions in the last year</text>')
    parts.append("</svg>")
    return "".join(parts)

def main():
    calendar = fetch_contributions(GITHUB_USERNAME, GITHUB_TOKEN)
    svg = build_svg(calendar, GITHUB_USERNAME)
    with open(OUTPUT_PATH, "w") as f:
        f.write(svg)
    print(f"Wrote {OUTPUT_PATH} — {calendar['totalContributions']} total contributions for {GITHUB_USERNAME}")

if __name__ == "__main__":
    main()
