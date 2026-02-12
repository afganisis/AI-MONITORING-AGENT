"""
Formatter for Telegram scan result messages.

Shows each visible error with date/time and status.
Hidden errors counted but not listed.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional

from app.services.error_classifier import error_classifier, HIDDEN_FROM_DISPLAY


SEVERITY_EMOJI = {
    "critical": "\U0001f534",
    "high": "\U0001f7e0",
    "medium": "\U0001f7e1",
    "low": "\U0001f7e2",
}

SEVERITY_ORDER = ["critical", "high", "medium", "low"]


def _fmt_time(error_time: Any) -> str:
    """Convert timestamp to 'DD.MM HH:MM'."""
    if not error_time:
        return ""
    try:
        if isinstance(error_time, (int, float)):
            ts = error_time / 1000 if error_time > 1e12 else error_time
            return datetime.fromtimestamp(ts).strftime("%d.%m %H:%M")
        elif isinstance(error_time, str):
            dt = datetime.fromisoformat(error_time.replace("Z", "+00:00"))
            return dt.strftime("%d.%m %H:%M")
    except Exception:
        pass
    return ""


def _classify(msg: str) -> Dict[str, str]:
    """Classify error message."""
    c = error_classifier.classify(msg)
    if c:
        return {"key": c.key, "name": c.name, "severity": c.severity.value}
    return {"key": "unknown", "name": msg[:50], "severity": "medium"}


def format_driver_results(
    driver_name: str,
    errors: List[Dict[str, Any]],
) -> str:
    """Format errors for one driver with date/time and status."""
    if not errors:
        return f"\u2705 {driver_name} \u2014 Clean"

    # Classify + extract details
    items = []
    for err in errors:
        msg = (
            err.get("errorMessage")
            or err.get("error_message")
            or err.get("message")
            or err.get("name")
            or "Unknown"
        )
        cl = _classify(msg)
        items.append({
            **cl,
            "time": _fmt_time(err.get("errorTime") or err.get("error_time") or err.get("timestamp")),
            "status": err.get("eventCode") or err.get("status") or "",
        })

    visible = [i for i in items if i["key"] not in HIDDEN_FROM_DISPLAY]
    hidden_count = len(items) - len(visible)
    total = len(items)

    lines = [f"\u26a0\ufe0f {driver_name} \u2014 {total} errors"]

    # Group by (severity, name)
    groups: Dict[str, Dict[str, list]] = {s: {} for s in SEVERITY_ORDER}
    for v in visible:
        sev, name = v["severity"], v["name"]
        if name not in groups[sev]:
            groups[sev][name] = []
        groups[sev][name].append(v)

    for sev in SEVERITY_ORDER:
        if not groups[sev]:
            continue
        emoji = SEVERITY_EMOJI[sev]
        for name, occurrences in groups[sev].items():
            cnt = len(occurrences)
            label = f"{name} x{cnt}" if cnt > 1 else name

            # Build detail: date/time + status from first occurrence
            first = occurrences[0]
            detail = ""
            if first["time"] or first["status"]:
                parts = [p for p in [first["time"], first["status"]] if p]
                detail = f" ({', '.join(parts)})"

            lines.append(f"  {emoji} {label}{detail}")

    if hidden_count > 0:
        lines.append(f"  \u2139\ufe0f +{hidden_count} info")

    return "\n".join(lines)


def format_scan_results(
    company_name: str,
    driver_results: List[Dict[str, Any]],
    scan_duration_sec: Optional[float] = None,
    employee_name: str = "",
    truck_unit: str = "",
    logbook_type: str = "",
    company_total_errors: Optional[int] = None,
) -> str:
    """Format full scan results for Telegram."""
    # Header
    parts = [f"\U0001f3e2 {company_name}"]
    if truck_unit:
        parts[0] += f" #{truck_unit}"

    meta = []
    if logbook_type:
        meta.append(logbook_type)
    if employee_name:
        meta.append(employee_name)
    if meta:
        parts.append(" | ".join(meta))

    lines = ["\n".join(parts), "\u2500" * 20, ""]

    total_errors = 0
    for dr in driver_results:
        driver_name = dr.get("driver_name", "Unknown")
        errors = dr.get("errors", [])
        total_errors += len(errors)

        lines.append(format_driver_results(driver_name, errors))

        scan_error = dr.get("scan_error")
        if scan_error:
            lines.append(f"  \u274c {scan_error[:80]}")

    # Footer
    lines.append("")
    lines.append("\u2500" * 20)
    if total_errors == 0:
        lines.append("\u2705 No errors found")
    else:
        dur = f" \u2022 {scan_duration_sec:.0f}s" if scan_duration_sec else ""
        lines.append(f"Total: {total_errors} errors{dur}")

    # Company overview from monitoring scan
    if company_total_errors is not None and company_total_errors > 0:
        lines.append(f"\U0001f50d Company total: {company_total_errors} errors")

    return "\n".join(lines)


def format_not_found_warning(not_found_lines: List[str]) -> str:
    """Format warning about unmatched lines."""
    if not not_found_lines:
        return ""
    lines = ["\u26a0\ufe0f Not found in DB:"]
    for line in not_found_lines:
        lines.append(f"  \u2022 {line}")
    return "\n".join(lines)
