#!/usr/bin/env python3
"""Manually audit public GitHub contributions, then render a static profile panel."""
import argparse
import datetime as dt
import html
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
LOGIN = "nixfred"
BEGIN = "<!-- BEGIN PUBLIC CONTRIBUTIONS -->"
END = "<!-- END PUBLIC CONTRIBUTIONS -->"
QUERY = '''query($from:DateTime!,$to:DateTime!){user(login:"nixfred"){
  contributionsCollection(from:$from,to:$to){
    totalRepositoriesWithContributedCommits
    commitContributionsByRepository(maxRepositories:100){
      repository{nameWithOwner isPrivate isFork}
      contributions(first:1){nodes{occurredAt commitCount url}}
    }
  }
}}'''


def api(endpoint, *args):
    result = json.loads(subprocess.check_output(["gh", "api", endpoint, *args], text=True))
    if isinstance(result, dict) and result.get("errors"):
        raise RuntimeError("GitHub returned GraphQL errors; refusing a partial audit")
    return result


def iso(value):
    return value.isoformat().replace("+00:00", "Z")


def audit(now):
    identity = api("user")
    if identity["login"].lower() != LOGIN:
        raise RuntimeError("Run this audit authenticated as nixfred")
    created = dt.datetime.fromisoformat(identity["created_at"].replace("Z", "+00:00"))
    windows, evidence = [], {}

    def entry(name):
        return evidence.setdefault(name, {"name": name, "calendar_urls": [], "credited_commit_dates": [], "merged_prs": []})

    def calendar(start, finish):
        response = api("graphql", "-f", "query=" + QUERY, "-f", "from=" + iso(start), "-f", "to=" + iso(finish))
        collection = response["data"]["user"]["contributionsCollection"]
        rows = collection["commitContributionsByRepository"]
        # Repository arrays have no cursor. Recursively reduce the date window
        # whenever either the aggregate or returned array could hit its cap.
        if collection["totalRepositoriesWithContributedCommits"] >= 100 or len(rows) >= 100:
            if (finish - start).total_seconds() <= 1:
                raise RuntimeError("Contribution window still capped; refusing incomplete data")
            midpoint = (start + (finish - start) / 2).replace(microsecond=0)
            calendar(start, midpoint)
            calendar(midpoint + dt.timedelta(seconds=1), finish)
            return
        windows.append({"from": iso(start), "to": iso(finish), "repository_cap": 100, "cap_reached": False})
        for row in rows:
            repo = row["repository"]
            if repo["isPrivate"] or repo["isFork"]:
                continue
            item = entry(repo["nameWithOwner"])
            for node in row["contributions"]["nodes"]:
                if node["commitCount"] > 0:
                    item["calendar_urls"].append(node["url"])
                    item["credited_commit_dates"].append(node["occurredAt"][:10])

    for year in range(created.year, now.year + 1):
        start = max(created, dt.datetime(year, 1, 1, tzinfo=dt.timezone.utc))
        finish = min(now, dt.datetime(year + 1, 1, 1, tzinfo=dt.timezone.utc) - dt.timedelta(seconds=1))
        calendar(start, finish)

    query = f"author:{LOGIN} is:pr is:merged is:public merged:<={iso(now)}"
    first = api("search/issues?" + urlencode({"q": query, "per_page": 100, "page": 1}))
    total = first["total_count"]
    # Current history fits under search's 1,000-result ceiling. Fail visibly
    # if it outgrows it instead of publishing a first-1,000 count.
    if total > 1000:
        raise RuntimeError("Merged PR search exceeds 1,000; partition the query before refreshing")
    pages = [first]
    for page in range(2, (total + 99) // 100 + 1):
        pages.append(api("search/issues?" + urlencode({"q": query, "per_page": 100, "page": page})))
    if any(page["incomplete_results"] or page["total_count"] != total for page in pages):
        raise RuntimeError("Incomplete or changing PR search; refusing a partial audit")
    pull_requests = [item for page in pages for item in page["items"]]
    if len(pull_requests) != total or len({pr["html_url"] for pr in pull_requests}) != total:
        raise RuntimeError("PR pagination mismatch")
    for pr in pull_requests:
        if pr["user"]["login"].lower() != LOGIN or not pr["pull_request"].get("merged_at"):
            raise RuntimeError("Search returned an unverified author or unmerged PR")
        name = pr["repository_url"].split("/repos/", 1)[1]
        entry(name)["merged_prs"].append(pr["html_url"])

    def public_metadata(item):
        repo = api("repos/" + item["name"])
        if repo["visibility"] != "public":
            return None
        canonical = repo["full_name"]
        if canonical.lower() != item["name"].lower():
            raise RuntimeError("Repository renamed during audit; reconcile evidence before publishing")
        return {
            "name": canonical, "url": repo["html_url"],
            "owned": repo["owner"]["login"].lower() == LOGIN,
            "archived": repo["archived"], "is_fork": repo["fork"],
            **{key: sorted(set(item[key])) for key in ("calendar_urls", "credited_commit_dates", "merged_prs")},
        }

    with ThreadPoolExecutor(max_workers=4) as pool:
        repos = [item for item in pool.map(public_metadata, evidence.values()) if item is not None]
    return {"schema_version": 1, "login": LOGIN, "verified_at": iso(now),
            "coverage_from": iso(created), "calendar_windows": windows,
            "merged_pr_search": {"query": query, "total_results": total, "pages": len(pages), "incomplete_results": False},
            "repositories": sorted(repos, key=lambda item: item["name"].lower())}


def table(repos):
    rows = ["| Public project | Verified evidence |", "| :--- | :--- |"]
    for repo in repos:
        evidence = []
        if repo["calendar_urls"]:
            evidence.append(f'[Credited commits]({repo["calendar_urls"][-1]})')
        if repo["merged_prs"]:
            evidence.append(f'[Merged PR]({repo["merged_prs"][0]}) ({len(repo["merged_prs"])})')
        flags = " · archived" if repo["archived"] else ""
        flags += " · fork with merged PR" if repo["is_fork"] else ""
        rows.append(f'| [{html.escape(repo["name"])}]({repo["url"]}){flags} | {" · ".join(evidence)} |')
    return "\n".join(rows)


def render(data):
    repos = data["repositories"]
    if len({r["name"].lower() for r in repos}) != len(repos):
        raise RuntimeError("Duplicate contributor projects")
    for repo in repos:
        assert repo["calendar_urls"] or repo["merged_prs"]
        assert repo["url"] == "https://github.com/" + repo["name"]
        assert not repo["is_fork"] or repo["merged_prs"]
    external = [r for r in repos if not r["owned"]]
    owned = [r for r in repos if r["owned"]]
    accepted = sum(bool(r["merged_prs"]) for r in external)
    date = data["verified_at"][:10]
    block = f'''{BEGIN}
## Open source contributions

[![{len(external)} external public projects; {len(repos)} including my repositories. Verified {date}. Static contribution snapshot.](assets/contributions.svg)](CONTRIBUTIONS.md)

**{len(external)} public projects outside `nixfred/` · {len(repos)} including my own repositories · {accepted} external projects with merged PRs.**

Counted from GitHub-credited commits and merged pull requests since October 2015. Ownership, forks alone, open requests, issues and reviews do not qualify. Organization-owned repositories count as outside my personal namespace. **[Full inventory, evidence and refresh method →](CONTRIBUTIONS.md)**

<details>
<summary>See all {len(external)} external contributor projects</summary>

{table(external)}

</details>

<sub>Public-only snapshot verified {date} (UTC). Refreshed manually; this panel does not update itself.</sub>
{END}'''
    readme = (ROOT / "README.md").read_text()
    if BEGIN in readme and END in readme:
        readme = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), lambda _: block, readme, flags=re.S)
    else:
        marker = '<img src="assets/desktop-chapter.svg"'
        if marker not in readme:
            raise RuntimeError("Profile insertion point missing")
        readme = readme.replace(marker, block + "\n\n" + marker, 1)

    doc = f'''# Public contribution projects

[← Back to the profile](README.md)

**{len(external)} external projects · {len(owned)} owned projects · {len(repos)} total.** Verified {data["verified_at"]}.

One project counts once when GitHub credits `nixfred` with a commit contribution in a public non-fork repository, or a public pull request authored by `nixfred` was merged there. Commit credit can include co-authorship and GitHub's rebase credit; it is not a claim of sole authorship. “External” means outside the personal `nixfred/` namespace, including organization-owned projects; it does not imply someone else owns the organization or that I am a current maintainer.

## External contributor projects

All {len(external)} are listed below. {accepted} have at least one accepted, merged PR; the remaining projects qualify through GitHub's credited commit history. The number beside a merged-PR link is the number of indexed merged PRs for that project, not a commit count.

{table(external)}

## Owned repositories with contributions

These {len(owned)} qualify through the same evidence rule. Ownership or creating a fork alone is insufficient. Archived projects retain their historical contributions and are labeled.

{table(owned)}

## Scope and limits

- The calendar audit starts at account creation on 29 October 2015 and ends at the verification timestamp. It queries every year and recursively splits windows that could reach GitHub's 100-repository array cap. No repository window was accepted at that cap.
- The public merged-PR search returned {data["merged_pr_search"]["total_results"]} unique results across {data["merged_pr_search"]["pages"]} pages, with no incomplete-results flag. It includes all indexed history through the snapshot time, not just the last year. Each counted repository's current public visibility was checked separately.
- Identity uses GitHub's canonical `nixfred` account attribution, covering account-linked commit identities and credited co-authors. No personal email address is queried or published. Unlinked historical identities cannot be inferred safely and are outside this count.
- Private, deleted or inaccessible repositories, unmerged requests, reviews and issues are excluded. Commit credit follows [GitHub's contribution rules](https://docs.github.com/en/account-and-profile/reference/profile-contributions-reference); this is a verified public snapshot, not a lifetime-completeness guarantee or a maintenance claim.
- Commit search alone can overcount copied histories. A supplemental [public commit search](https://github.com/search?q=author%3Anixfred+is%3Apublic+-user%3Anixfred&type=commits) found identical commit SHAs in downstream copies of Omastorm, Flea and Omavoice. Those copied-history matches do not qualify as additional projects under this panel's evidence rule. Nor are indexed author-only matches without calendar credit or a merged PR.
- The calendar evidence links show the month on the public profile; expand that month's commit activity to inspect the repository. Merged-PR links point to a concrete accepted request. GitHub may index new activity later, and public visibility can change after the audit.

## Manual refresh

Run `python3 tools/refresh_contributions.py --refresh` with `gh` authenticated as `nixfred`. It uses read-only GitHub APIs and updates `data/public-contributions.json`, this document, the existing README section and `assets/contributions.svg`. Without `--refresh`, it renders the saved public snapshot offline.

The refresh fails rather than publishing incomplete search results or a repository-cap truncation. If merged-PR history grows beyond 1,000 results, partition the search before refreshing. No workflow, schedule, new credential, visitor tracker or external image service is configured. Review and publish refreshed files deliberately.
'''
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="350" viewBox="0 0 1400 350" role="img" aria-labelledby="title desc"><title id="title">Open source contributions — {len(external)} external public projects</title><desc id="desc">{len(repos)} public projects including owned repositories; {accepted} external projects with merged pull requests. Verified {date}. Static manual snapshot.</desc><rect width="1400" height="350" rx="22" fill="#080e17"/><path d="M28 28V322M1372 28V322" stroke="#62fff1" stroke-width="3"/><g font-family="Arial,Helvetica,sans-serif"><text x="66" y="67" fill="#c4cfdb" font-size="25" letter-spacing="4">OPEN SOURCE / CONTRIBUTIONS</text><text x="61" y="246" fill="#62fff1" font-size="182" font-weight="900">{len(external)}</text><text x="316" y="159" fill="#f4f0e7" font-size="49" font-weight="800">EXTERNAL</text><text x="316" y="217" fill="#f4f0e7" font-size="49" font-weight="800">PUBLIC PROJECTS</text><path d="M832 98V258" stroke="#3e586a" stroke-width="2"/><text x="879" y="151" fill="#ffae73" font-size="60" font-weight="800">{len(repos)}</text><text x="1040" y="145" fill="#c4cfdb" font-size="25">INCLUDING OWNED</text><text x="879" y="239" fill="#b49cff" font-size="60" font-weight="800">{accepted}</text><text x="1040" y="220" fill="#c4cfdb" font-size="25">EXTERNAL PROJECTS</text><text x="1040" y="249" fill="#c4cfdb" font-size="25">WITH MERGED PRs</text><text x="66" y="314" fill="#c4cfdb" font-size="23" letter-spacing="2">2015–{date[:4]} / PUBLIC ONLY / VERIFIED {date} / MANUAL SNAPSHOT</text></g></svg>'''
    (ROOT / "README.md").write_text(readme)
    (ROOT / "CONTRIBUTIONS.md").write_text(doc)
    (ROOT / "assets/contributions.svg").write_text(svg + "\n")
    print(f"Verified public projects: {len(external)} external, {len(owned)} owned, {len(repos)} total; {accepted} external with merged PRs")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Read public GitHub evidence using authenticated gh; otherwise render offline")
    args = parser.parse_args()
    path = ROOT / "data/public-contributions.json"
    if args.refresh:
        data = audit(dt.datetime.now(dt.timezone.utc).replace(microsecond=0))
        path.write_text(json.dumps(data, indent=2) + "\n")
    else:
        data = json.loads(path.read_text())
    render(data)
