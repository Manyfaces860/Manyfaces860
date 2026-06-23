from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

GRAPHQL_ENDPOINT = "https://api.github.com/graphql"

QUERY = """
query ContributionCalendar($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            contributionLevel
            weekday
          }
        }
      }
    }
  }
}
"""


@dataclass(frozen=True)
class ContributionDay:
    date: str
    count: int
    level: str
    weekday: int
    week_index: int


@dataclass(frozen=True)
class ContributionCalendar:
    username: str
    total_contributions: int
    weeks: list[list[ContributionDay]]


def fetch_calendar(username: str, token: str) -> ContributionCalendar:
    payload = json.dumps({"query": QUERY, "variables": {"login": username}}).encode("utf-8")
    request = urllib.request.Request(
        GRAPHQL_ENDPOINT,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "ccg-contribution-art-generator",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result: dict[str, Any] = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub GraphQL failed with HTTP {exc.code}: {details}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach GitHub GraphQL: {exc}") from exc

    if result.get("errors"):
        raise RuntimeError(f"GitHub GraphQL returned errors: {result['errors']}")

    user = result.get("data", {}).get("user")
    if user is None:
        raise RuntimeError(f"GitHub user '{username}' was not found.")

    raw_calendar = user["contributionsCollection"]["contributionCalendar"]
    weeks: list[list[ContributionDay]] = []
    for week_index, raw_week in enumerate(raw_calendar["weeks"]):
        weeks.append([
            ContributionDay(
                date=raw_day["date"],
                count=int(raw_day["contributionCount"]),
                level=raw_day["contributionLevel"],
                weekday=int(raw_day["weekday"]),
                week_index=week_index,
            )
            for raw_day in raw_week["contributionDays"]
        ])

    return ContributionCalendar(
        username=username,
        total_contributions=int(raw_calendar["totalContributions"]),
        weeks=weeks,
    )


def calendar_from_environment() -> ContributionCalendar:
    username = os.environ.get("GITHUB_USERNAME", "").strip()
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not username:
        raise RuntimeError("GITHUB_USERNAME is not set.")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is not set.")
    return fetch_calendar(username, token)
