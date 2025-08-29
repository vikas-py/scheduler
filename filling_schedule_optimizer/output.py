# output.py
# HTML report generation for the filling line scheduling tool

from .models import ScheduleEntry
from typing import List, Dict
import datetime

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
			<tr>{''.join(f'<th>{k}</th>' for k in metrics_hrs.keys())}</tr>
			<tr>{''.join(f'<td>{v}</td>' for v in metrics_hrs.values())}</tr>
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
