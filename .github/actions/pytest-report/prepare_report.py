"""Splits xfailed and superseded tests out of pytest's junit xml for the pytest-report action.

dorny/test-reporter only knows passed, failed and skipped tests, and pytest writes xfailed tests as skipped. This script
runs before dorny: it takes the xfailed tests out of the reports, so dorny's skipped count holds real skips only, and
writes the check run's title and summary with the xfailed and superseded counts added, in dorny's own format, for the
action's last step to put on the check run. Superseded upstream tests (notifynl-utils'
notifications_utils/testing_nl/superseded_tests.py) aren't in a report at all, only counted in a `superseded` property.
"""

import glob
import json
import os
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass, fields
from pathlib import Path

COUNTS = ("passed", "failed", "skipped", "xfailed", "superseded")
ICONS = {"passed": "✅", "failed": "❌", "skipped": "⚪", "xfailed": "🟢", "superseded": "🟢"}


@dataclass
class Counts:
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    xfailed: int = 0
    superseded: int = 0
    ms: float = 0


def split_report(path: Path) -> Counts:
    """Take the xfailed tests out of the report and count its tests the way dorny does."""
    tree = ET.parse(path)
    root = tree.getroot()
    counts = Counts()
    for suite in list(root.iter("testsuite")):
        xfailed = [c for c in suite.findall("testcase") if c.find("skipped[@type='pytest.xfail']") is not None]
        for case in xfailed:
            suite.remove(case)
        for attr in ("tests", "skipped"):
            suite.set(attr, str(int(suite.get(attr, 0)) - len(xfailed)))
        counts.xfailed += len(xfailed)
        for case in suite.findall("testcase"):
            if case.find("failure") is not None or case.find("error") is not None:
                counts.failed += 1
            elif case.find("skipped") is not None:
                counts.skipped += 1
            else:
                counts.passed += 1
        counts.ms += float(suite.get("time", 0)) * 1000
    if run_time := root.get("time"):  # dorny takes the run time from <testsuites> when it has one
        counts.ms = float(run_time) * 1000
    if (superseded := root.find(".//property[@name='superseded']")) is not None:
        counts.superseded = int(superseded.get("value", 0))
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return counts


def title(total: Counts) -> str:
    parts = [f"{total.passed} passed", f"{total.failed} failed", f"{total.skipped} skipped"]
    parts += [f"{n} {name}" for name in ("xfailed", "superseded") if (n := getattr(total, name))]
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def shields(text: str) -> str:
    return urllib.parse.quote(text, safe="").replace("-", "--").replace("_", "__")


def badge(total: Counts, badge_title: str) -> str:
    message = ", ".join(f"{n} {name}" for name in COUNTS if (n := getattr(total, name))) or "none"
    color = "critical" if total.failed else "yellow" if not total.passed else "success"
    hint = "Tests failed" if total.failed else "Tests passed successfully"
    return f"![{hint}](https://img.shields.io/badge/{shields(badge_title)}-{shields(message)}-{color})"


def format_time(ms: float) -> str:
    return f"{round(ms / 1000)}s" if ms > 1000 else f"{round(ms)}ms"


def summary(reports: list[tuple[str, Counts]], total: Counts, badge_title: str) -> str:
    lines = [badge(total, badge_title)]
    collapsed = not total.failed  # dorny's collapsed: auto
    if collapsed:
        lines += ["<details><summary>Expand for details</summary>", " "]
    lines += ["|Report|Passed|Failed|Skipped|Xfailed|Superseded|Time|", "|:---|---:|---:|---:|---:|---:|---:|"]
    for path, counts in reports:
        if any(getattr(counts, name) for name in COUNTS):
            cells = [f"{n} {ICONS[name]}" if (n := getattr(counts, name)) else "" for name in COUNTS]
            lines.append("|" + "|".join([path, *cells, format_time(counts.ms)]) + "|")
    if collapsed:
        lines.append("</details>")
    return "\n".join(lines)


def main() -> None:
    patterns = [pattern.strip() for pattern in os.environ["REPORT_PATH"].split(",")]
    paths = sorted({path for pattern in patterns for path in glob.glob(pattern, recursive=True)})
    if not paths:
        print(f"No junit xml matches {os.environ['REPORT_PATH']}")
        return
    reports = [(path, split_report(Path(path))) for path in paths]
    total = Counts(**{f.name: sum(getattr(counts, f.name) for _, counts in reports) for f in fields(Counts)})
    output = {"title": title(total), "summary": summary(reports, total, os.environ["BADGE_TITLE"])}
    Path(os.environ["OUTPUT_FILE"]).write_text(json.dumps({"output": output}), encoding="utf-8")
    print(output["title"])


if __name__ == "__main__":
    main()
