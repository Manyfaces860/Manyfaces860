from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path

from fetch_contributions import ContributionCalendar, ContributionDay

CELL_SIZE = 11
CELL_GAP = 4
PITCH = CELL_SIZE + CELL_GAP
LEFT = 58
TOP = 54
BOTTOM = 55
RIGHT = 24

LEVEL_COLORS = {
    "NONE": "#171717",
    "FIRST_QUARTILE": "#45101b",
    "SECOND_QUARTILE": "#82152b",
    "THIRD_QUARTILE": "#bd1838",
    "FOURTH_QUARTILE": "#ff234b",
}


@dataclass(frozen=True)
class GridGeometry:
    width: int
    height: int
    graph_width: int
    graph_height: int


def geometry(calendar: ContributionCalendar) -> GridGeometry:
    graph_width = max(1, len(calendar.weeks)) * PITCH - CELL_GAP
    graph_height = 7 * PITCH - CELL_GAP
    return GridGeometry(
        width=LEFT + graph_width + RIGHT,
        height=TOP + graph_height + BOTTOM,
        graph_width=graph_width,
        graph_height=graph_height,
    )


def cell_xy(day: ContributionDay) -> tuple[int, int]:
    return LEFT + day.week_index * PITCH, TOP + day.weekday * PITCH


def cell_center(day: ContributionDay) -> tuple[float, float]:
    x, y = cell_xy(day)
    return x + CELL_SIZE / 2, y + CELL_SIZE / 2


def serpentine_days(calendar: ContributionCalendar) -> list[ContributionDay]:
    ordered: list[ContributionDay] = []
    for week_index, week in enumerate(calendar.weeks):
        days = sorted(week, key=lambda day: day.weekday)
        if week_index % 2 == 1:
            days.reverse()
        ordered.extend(days)
    return ordered


def all_days(calendar: ContributionCalendar) -> list[ContributionDay]:
    return [day for week in calendar.weeks for day in week]


def rounded_cell(day: ContributionDay, inner: str = "") -> str:
    x, y = cell_xy(day)
    fill = LEVEL_COLORS.get(day.level, LEVEL_COLORS["NONE"])
    title = escape(f"{day.date}: {day.count} contributions")
    return (
        f'<rect x="{x}" y="{y}" width="{CELL_SIZE}" height="{CELL_SIZE}" '
        f'rx="2" fill="{fill}"><title>{title}</title>{inner}</rect>'
    )


def svg_open(calendar: ContributionCalendar, title: str) -> str:
    geo = geometry(calendar)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{geo.width}" height="{geo.height}" '
        f'viewBox="0 0 {geo.width} {geo.height}" role="img" aria-labelledby="title description">\n'
        f'  <title id="title">{escape(title)}</title>\n'
        f'  <desc id="description">{calendar.total_contributions} contributions by {escape(calendar.username)}</desc>\n'
    )


def labels(calendar: ContributionCalendar, status: str) -> str:
    geo = geometry(calendar)
    return f'''  <text x="{LEFT}" y="25" fill="#f3f3f3" font-family="monospace" font-size="13" font-weight="700">FIELD ACTIVITY // {escape(calendar.username.upper())}</text>
  <text x="{geo.width - RIGHT}" y="25" text-anchor="end" fill="#e5152e" font-family="monospace" font-size="11">{escape(status)}</text>
  <text x="{LEFT}" y="{geo.height - 18}" fill="#777777" font-family="monospace" font-size="10">TOTAL RECORDS: {calendar.total_contributions}</text>
'''


def write_svg(path: str | Path, content: str) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
