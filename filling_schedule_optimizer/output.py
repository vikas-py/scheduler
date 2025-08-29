# output.py
# HTML report generation for the filling line scheduling tool

from .models import ScheduleEntry
from typing import List, Dict, Tuple
import datetime

def _safe_hours(minutes: float | int | None) -> float | str:
    if minutes is None:
        return ""
    try:
        return round(float(minutes) / 60.0, 2)
    except Exception:
        return ""

def generate_html_report(schedule: List[ScheduleEntry], metrics: Dict, output_path: str):
    """
    Generate an HTML report summarizing the schedule and metrics.

    - Derives KPIs from the schedule when possible.
    - Uses values from `metrics` as fallbacks (or to override if you already computed them).
    - Expects ScheduleEntry fields:
        event_type, lot_id, lot_type, start_time, end_time, duration_minutes, notes
    """

    # --- Derive KPIs from schedule (robust to missing/None values) ---
    fills = [e for e in schedule if (getattr(e, "event_type", "") or "").upper() == "FILL" or getattr(e, "lot_id", None)]
    changeovers = [e for e in schedule if (getattr(e, "event_type", "") or "").upper() == "CHANGEOVER"]
    recleans = [e for e in schedule if (getattr(e, "event_type", "") or "").upper() == "RECLEAN"]

    # Timespan window
    start_times = [e.start_time for e in schedule if getattr(e, "start_time", None)]
    end_times = [e.end_time for e in schedule if getattr(e, "end_time", None)]
    first_start = min(start_times) if start_times else None
    last_end = max(end_times) if end_times else None

    # Busy & idle
    total_busy_min = sum((e.duration_minutes or 0) for e in schedule if e.duration_minutes)
    total_window_min = 0
    if first_start and last_end:
        total_window_min = max(0, (last_end - first_start).total_seconds() / 60.0)
    idle_time_hours = round(max(0.0, (total_window_min - total_busy_min)) / 60.0, 2) if total_window_min else ""

    # Fill stats
    fill_minutes = [e.duration_minutes for e in fills if e.duration_minutes]
    avg_fill = round(sum(fill_minutes) / len(fill_minutes) / 60.0, 2) if fill_minutes else ""
    max_fill = round(max(fill_minutes) / 60.0, 2) if fill_minutes else ""
    min_fill = round(min(fill_minutes) / 60.0, 2) if fill_minutes else ""

    # Utilization
    utilization = ""
    if total_window_min:
        utilization = round((total_busy_min / total_window_min) * 100.0, 1)

    # Same/Diff changeovers by note text (best-effort classification)
    same_type = 0
    diff_type = 0
    same_type_time_min = 0.0
    diff_type_time_min = 0.0
    for e in changeovers:
        note = (e.notes or "").lower()
        dur = e.duration_minutes or 0
        if "same" in note:
            same_type += 1
            same_type_time_min += dur
        elif "diff" in note or "different" in note or "type change" in note:
            diff_type += 1
            diff_type_time_min += dur
        else:
            # If unspecified, just count it under changeovers but not in same/diff buckets
            html = f"""
        <html>
        <head>
            <title>Filling Line Schedule Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #2c3e50; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; }}
                th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
                th {{ background: #f4f4f4; }}
                tr:nth-child(even) {{ background: #fafafa; }}
            </style>
        </head>
        <body>
            <h1>Filling Line Schedule Report</h1>
            <h2>Summary KPIs</h2>
            <table>
                <tr>{''.join(f'<th>{k}</th>' for k in all_kpis.keys())}</tr>
                <tr>{''.join(f'<td>{v}</td>' for v in all_kpis.values())}</tr>
            </table>
            <h2>Detailed Schedule</h2>
            <table>
                <tr>
                    <th>Event</th>
                    <th>Lot ID</th>
                    <th>Lot Type</th>
                    <th>Start Time</th>
                    <th>End Time</th>
                    <th>Duration (hours)</th>
                    <th>Notes</th>
                </tr>
        """
            for entry in schedule:
                # Match the requested format: reclean/changeover may have empty Lot ID, Lot Type, etc.
                event = entry.event_type or ''
                lot_id = entry.lot_id or ''
                lot_type = entry.lot_type or ''
                # Use the requested time format: YYYY-MM-DD HH:MM (with leading zeroes)
                time_fmt = '%Y-%m-%d %H:%M'
                start_time = entry.start_time.strftime(time_fmt) if entry.start_time else ''
                end_time = entry.end_time.strftime(time_fmt) if entry.end_time else ''
                # Always show duration in hours, rounded to 2 decimals
                duration_hrs = f"{round(entry.duration_minutes/60, 2):.2f}" if entry.duration_minutes is not None else ''
                notes = entry.notes or ''
                html += f"""
                <tr>
                    <td>{event}</td>
                    <td>{lot_id}</td>
                    <td>{lot_type}</td>
                    <td>{start_time}</td>
                    <td>{end_time}</td>
                    <td>{duration_hrs}</td>
                    <td>{notes}</td>
                </tr>
                """
            html += f"""
            </table>
            <p>Report generated on: {{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}}</p>
        </body>
        </html>
        """

    # Inject any already-hour/percent/count metrics (won’t convert; will override if keys match)
    # You can pass keys identical to those in derived_kpis to override, or add new ones.
    for k, v in metrics.items():
        if k in merged_kpis:
            merged_kpis[k] = v

    # --- Build HTML ---
    html = [
        "<html>",
        "<head>",
        "<title>Filling Line Schedule Report</title>",
        "<style>",
        "body { font-family: Arial, sans-serif; margin: 40px; }",
        "h1 { color: #2c3e50; }",
        "table { border-collapse: collapse; width: 100%; margin-bottom: 30px; }",
        "th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }",
        "th { background: #f4f4f4; }",
        "tr:nth-child(even) { background: #fafafa; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Filling Line Schedule Report</h1>",
        "<h2>Summary KPIs</h2>",
        "<table>",
        "<tr>" + "".join(f"<th>{k}</th>" for k in merged_kpis.keys()) + "</tr>",
        "<tr>" + "".join(f"<td>{merged_kpis[k]}</td>" for k in merged_kpis.keys()) + "</tr>",
        "</table>",
        "<h2>Detailed Schedule</h2>",
        "<table>",
        "<tr>",
        "<th>Event</th>",
        "<th>Lot ID</th>",
        "<th>Lot Type</th>",
        "<th>Start Time</th>",
        "<th>End Time</th>",
        "<th>Duration (hours)</th>",
        "<th>Notes</th>",
        "</tr>",
    ]

    for entry in schedule:
        duration_hrs = _safe_hours(getattr(entry, "duration_minutes", None))
        event_type = getattr(entry, "event_type", "") or ""
        lot_id = getattr(entry, "lot_id", "") or ""
        lot_type = getattr(entry, "lot_type", "") or ""
        st = getattr(entry, "start_time", None)
        et = getattr(entry, "end_time", None)
        notes = getattr(entry, "notes", "") or ""
        st_txt = st.strftime("%Y-%m-%d %H:%M") if st else ""
        et_txt = et.strftime("%Y-%m-%d %H:%M") if et else ""

        html.append(
            "<tr>"
            f"<td>{event_type}</td>"
            f"<td>{lot_id}</td>"
            f"<td>{lot_type}</td>"
            f"<td>{st_txt}</td>"
            f"<td>{et_txt}</td>"
            f"<td>{duration_hrs}</td>"
            f"<td>{notes}</td>"
            "</tr>"
        )

    html.extend([
        "</table>",
        f"<p>Report generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</p>",
        "</body>",
        "</html>",
    ])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html))
