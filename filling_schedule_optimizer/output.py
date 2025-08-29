# output.py
# HTML report generation for the filling line scheduling tool


from .models import ScheduleEntry
from typing import List, Dict
import datetime
import statistics

def generate_html_report(schedule: List[ScheduleEntry], metrics: Dict, output_path: str):
	"""
	Generate an HTML report summarizing the schedule and metrics.
	"""
	# Convert all metrics from minutes to hours and improve KPI labels
	kpi_map = {
		'Total Time (min)': 'Total Schedule Time (hours)',
		'Total Changeover Time (min)': 'Total Changeover Time (hours)',
		'Total Reclean Time (min)': 'Total Reclean Time (hours)',
		'Total Fill Time (min)': 'Total Filling Time (hours)'
	}
	metrics_hrs = {kpi_map.get(k, k): round(v/60, 2) for k, v in metrics.items()}

	# --- Additional KPIs ---
	fill_entries = [e for e in schedule if e.event_type == 'fill']
	changeover_entries = [e for e in schedule if e.event_type == 'changeover']
	reclean_entries = [e for e in schedule if e.event_type == 'reclean']
	fill_times = [e.duration_minutes/60 for e in fill_entries if e.duration_minutes]
	num_lots = len(fill_entries)
	num_changeovers = len(changeover_entries)
	num_recleans = len(reclean_entries)
	avg_fill = round(statistics.mean(fill_times), 2) if fill_times else 0
	max_fill = round(max(fill_times), 2) if fill_times else 0
	min_fill = round(min(fill_times), 2) if fill_times else 0
	utilization = round((metrics.get('Total Fill Time (min)', 0) / metrics.get('Total Time (min)', 1)) * 100, 2)
	idle_time = round((metrics.get('Total Time (min)', 0) - metrics.get('Total Fill Time (min)', 0))/60, 2)
	# Changeover breakdown
	same_type = sum(1 for e in changeover_entries if e.duration_minutes and e.duration_minutes <= 4*60)
	diff_type = sum(1 for e in changeover_entries if e.duration_minutes and e.duration_minutes > 4*60)
	same_type_time = round(sum(e.duration_minutes for e in changeover_entries if e.duration_minutes and e.duration_minutes <= 4*60)/60, 2)
	diff_type_time = round(sum(e.duration_minutes for e in changeover_entries if e.duration_minutes and e.duration_minutes > 4*60)/60, 2)
	# Schedule span
	first_start = min((e.start_time for e in schedule if e.start_time), default=None)
	last_end = max((e.end_time for e in schedule if e.end_time), default=None)

	# Compose additional KPIs
	extra_kpis = {
		'Number of Lots Scheduled': num_lots,
		'Number of Changeovers': num_changeovers,
		'Number of Recleans': num_recleans,
		'Average Lot Fill Time (hours)': avg_fill,
		'Maximum Lot Fill Time (hours)': max_fill,
		'Minimum Lot Fill Time (hours)': min_fill,
		'Utilization (%)': utilization,
		'Total Idle Time (hours)': idle_time,
		'Same-Type Changeovers': same_type,
		'Diff-Type Changeovers': diff_type,
		'Same-Type Changeover Time (hours)': same_type_time,
		'Diff-Type Changeover Time (hours)': diff_type_time,
		'First Start Time': first_start.strftime('%Y-%m-%d %H:%M') if first_start else '',
		'Last End Time': last_end.strftime('%Y-%m-%d %H:%M') if last_end else ''
	}

	# Merge KPIs for display
	all_kpis = {**metrics_hrs, **extra_kpis}

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
	for entry in schedule:
		duration_hrs = round(entry.duration_minutes/60, 2) if entry.duration_minutes else ''
		html += f"""
			<tr>
				<td>{entry.event_type}</td>
				<td>{entry.lot_id or ''}</td>
				<td>{entry.lot_type or ''}</td>
				<td>{entry.start_time.strftime('%Y-%m-%d %H:%M') if entry.start_time else ''}</td>
				<td>{entry.end_time.strftime('%Y-%m-%d %H:%M') if entry.end_time else ''}</td>
				<td>{duration_hrs}</td>
				<td>{entry.notes or ''}</td>
			</tr>
		"""
	html += """
		</table>
		<p>Report generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
	</body>
	</html>
	"""
	with open(output_path, 'w') as f:
		f.write(html)
