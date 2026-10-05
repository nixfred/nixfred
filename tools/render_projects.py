#!/usr/bin/env python3
"""Render the public-only inventory snapshot into the profile's project catalog."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DERIVED = {
    "Glide": ("feschber/lan-mouse", "Powered by Lan Mouse"),
    "swish": ("h3rmt/hyprshell", "Built on hyprshell"),
    "omarchy-chronos": ("omacom/omarchy", "Extends the stock Omarchy clock"),
    "nixvibes": ("cloudflare/vibesdk", "Based on Cloudflare VibeSDK"),
}
SUMMARIES = {
    "shipyard": "Local Git commit activity in the Omarchy bar.",
    "dockyard.omarchy": "Docker container cockpit for Omarchy.",
    "sentinel.omarchy": "Systemd service and journal watchdog for Omarchy.",
    "tomato.omarchy": "Pomodoro focus timer for Omarchy.",
    "pingboard.omarchy": "LAN, ISP, DNS and tailnet path diagnostics for Omarchy.",
    "daylight.omarchy": "Local sun and moon calculations for Omarchy.",
    "pr.hunter": "GitHub project inspection and existing-agent brief handoff.",
    "sandman": "Screen blanking and idle management for Linux.",
    "omarchy-port-doctor": "Port inspection tools for Omarchy.",
    "omarchy-rclone": "Cloud mount controls in the Omarchy bar.",
    "MeetingNotes": "Meeting notes project; see upstream documentation.",
    "PwGen": "Password generator project.",
    "magicvm": "Virtual machine creation project.",
    "lastpass-ssh-restore": "SSH restoration tooling.",
    "x.api": "X API tooling.",
    "nixfred.cloud": "Web project; see repository documentation.",
    "blamethe.tech": "Web project; see repository documentation.",
    "nixfred.com.v5": "Personal site iteration.",
    "resume.nixfred.com.ninjaone": "Prior web presentation project.",
    "masonnix.com": "Personal web presentation project.",
    "nextstep": "Interactive web presentation.",
    "ai": "AI infrastructure portfolio site.",
    "quantum": "Interactive quantum computing essay.",
    "galaxy.nixfred.com": "Interactive Three.js map of public projects.",
    "ghostdrive": "Portable offline AI with Ollama.",
    "nixvibes": "AI web application generator based on Cloudflare VibeSDK.",
    "Glide": "LAN mouse and keyboard sharing for Omarchy.",
    "omarchy-chronos": "Animated clock and calendar for Omarchy.",
    "swish": "Workspace switcher for Omarchy and Hyprland.",
    "omarchy.nixfred.com": "Omarchy plugin catalog with public repository and marketplace metadata.",
    "apple-health-dashboard": "Self-hosted dashboard software for Apple Health exports.",
    "claude-on-mac": "Apple ecosystem tools for Claude Code with messaging consent controls.",
    "pulse": "CPU, memory, storage, network and GPU monitoring for Omarchy.",
    "rift": "Workspace app recall for Omarchy.",
    "autocorrect.omarchy": "Global autocorrect for Omarchy using fcitx5; work in progress.",
}


def cell(value):
    return html.escape(str(value), quote=False).replace("|", "&#124;").replace("\n", " ")


def row(repo, fork_table=False):
    name = repo["name"]
    link = f'**[{cell(name)}]({repo["html_url"]})**'
    summary = SUMMARIES.get(name) or repo["description"] or "No public repository description supplied."
    if len(summary) > 160:
        summary = summary[:157].rsplit(" ", 1)[0] + "…"
    if name in DERIVED:
        source, credit = DERIVED[name]
        summary = cell(summary) + f' {credit}: [{source}](https://github.com/{source}).'
    else:
        summary = cell(summary)
    pushed = repo["pushed_at"][:10] if repo["pushed_at"] else "Not reported"
    if fork_table:
        parent = repo["parent"]
        return f'| {link} | [{cell(parent)}](https://github.com/{parent}) | {summary} | {pushed} |'
    if repo["fork"]:
        parent = repo["parent"]
        summary += f' Fork of [{cell(parent)}](https://github.com/{parent}).'
    return f'| {link} | {summary} | {pushed} |'


def render():
    data = json.loads((ROOT / "data/public-projects.json").read_text())
    repos = data["repositories"]
    assert len({r["name"].casefold() for r in repos}) == len(repos)
    for repo in repos:
        assert repo["html_url"] == "https://github.com/nixfred/" + repo["name"]
        assert not repo["fork"] or repo.get("parent")
    sections = [
        ("Recent pushes · independent repositories", [r for r in repos if not r["fork"] and not r["archived"] and r["pushed_at"] and r["pushed_at"] >= "2026-09-01"], False),
        ("Earlier work and experiments · independent repositories", [r for r in repos if not r["fork"] and not r["archived"] and (not r["pushed_at"] or r["pushed_at"] < "2026-09-01")], False),
        ("Forks and upstream credit", [r for r in repos if r["fork"] and not r["archived"]], True),
        ("Archived repositories", [r for r in repos if r["archived"]], False),
    ]
    assert sum(len(group) for _, group, _ in sections) == len(repos)
    lines = ["# Public project catalog", "", "[← Back to the profile](README.md)", "",
             f'**{len(repos)} public repositories · verified {data["verified_on"]} (UTC).**', "",
             "This is a dated snapshot of GitHub's public repository metadata. Last push means a repository received a push; it does not prove ongoing maintenance, a release, local use, or authorship. Forks can include upstream updates. Check each repository before installing.", "",
             "Independent means GitHub does not mark the repository as a fork. It does not imply sole authorship: known derived projects have explicit credit. The archive follows GitHub's archived flag. Older unarchived work stays visible as earlier work and experiments, without an active-maintenance claim.", "",
             "[Recent pushes](#recent-pushes--independent-repositories) · [Earlier work](#earlier-work-and-experiments--independent-repositories) · [Forks](#forks-and-upstream-credit) · [Archive](#archived-repositories)", ""]
    for title, group, fork_table in sections:
        lines += [f"## {title}", "", f"{len(group)} repositories.", ""]
        if fork_table:
            lines += ["The upstream column names the immediate parent reported by GitHub. Credit belongs to those projects and their contributors; this listing makes no claim that every fork has local modifications or contributed fixes upstream.", "",
                      "| Repository | Upstream / original project | Public summary | Last push (UTC) |", "| :--- | :--- | :--- | :--- |"]
        else:
            lines += ["| Repository | Public summary | Last push (UTC) |", "| :--- | :--- | :--- |"]
        lines += [row(repo, fork_table) for repo in sorted(group, key=lambda r: r["name"].casefold())] + [""]
    lines += ["## Refreshing this catalog", "", "The public snapshot lives in `data/public-projects.json`. Update it from GitHub's public `users/nixfred/repos` endpoint with pagination; retain only the fields already in this file. For forks, verify the parent using the public repository endpoint. Never populate this catalog from private repositories or local machine inventories.", "", "Then run `python3 tools/render_projects.py` and review the Markdown. Summaries come from public descriptions or the documented neutral overrides in the renderer. The September 2026 boundary groups this audit by recency; move it deliberately for a later audit. No background job, tracking widget or machine access is required.", ""]
    (ROOT / "PROJECTS.md").write_text("\n".join(lines))


if __name__ == "__main__":
    render()
