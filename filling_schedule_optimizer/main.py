# main.py
# Command-line workflow engine for the filling line scheduling tool

import sys
import csv
from . import config
from .models import Lot
from .validation import validate_lots
from .output import generate_html_report

def load_lots_from_csv(filepath):
	lots = []
	with open(filepath, newline='') as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			lots.append(Lot(
				id=row.get('Lot ID'),
				type=row.get('Type'),
				vials=int(row.get('Vials', 0)),
				description=None
			))
	return lots

def main():
	print("--- Filling Line Scheduling Tool ---")
	print("Loading configuration...")
	print(f"Data file: {config.DATA_FILE}")
	print(f"Report file: {config.REPORT_FILE}")
	print(f"Strategy: {config.SCHEDULING_STRATEGY}")

	print("Loading lots data...")
	lots = load_lots_from_csv(config.DATA_FILE)

	print("Validating lots data...")
	errors = validate_lots(lots)
	if errors:
		print("Validation errors found:")
		for err in errors:
			print(f"  - {err}")
		sys.exit(1)
	print("Data validation passed.")

	print("Generating schedule...")
	if config.SCHEDULING_STRATEGY == 'fifo':
		from .strategies.fifo import generate_schedule
	elif config.SCHEDULING_STRATEGY == 'spt_only':
		from .strategies.spt_only import generate_schedule
	else:
		from .strategies.hybrid_heuristic import generate_schedule

	schedule, metrics = generate_schedule(lots, config)
	print("Schedule generated.")

	print("Generating HTML report...")
	generate_html_report(schedule, metrics, config.REPORT_FILE)
	print(f"Report saved to {config.REPORT_FILE}")
	print("--- Done ---")

if __name__ == "__main__":
	main()
