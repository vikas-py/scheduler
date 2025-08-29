# hybrid_heuristic.py
# Hybrid heuristic scheduling strategy for the filling line scheduling tool

from typing import List, Tuple, Dict
from ..models import Lot, ScheduleEntry
import datetime

def generate_schedule(lots: List[Lot], config) -> Tuple[List[ScheduleEntry], Dict]:
	"""
	Hybrid heuristic: group by type, sort by SPT within group, greedy group order, insert changeovers and recleans.
	Returns (schedule, metrics).
	"""
	# 1. Group lots by type
	from collections import defaultdict
	type_groups = defaultdict(list)
	for lot in lots:
		type_groups[lot.type].append(lot)

	# 2. Sort each group by SPT (shortest fill time first)
	for t in type_groups:
		type_groups[t].sort(key=lambda lot: lot.vials / config.FILLING_RATE_VIALS_PER_MIN)

	# 3. Greedy: order groups by total run time (largest first)
	group_order = sorted(type_groups.keys(), key=lambda t: -sum(lot.vials for lot in type_groups[t]))

	schedule = []
	# Use configured start datetime if set
	if hasattr(config, 'SCHEDULE_START_DATETIME') and config.SCHEDULE_START_DATETIME:
		now = datetime.datetime.strptime(config.SCHEDULE_START_DATETIME, '%Y-%m-%d %H:%M')
	else:
		now = datetime.datetime.now()
	current_time = now
	# Always start with a reclean
	schedule.append(ScheduleEntry(
		event_type='reclean',
		start_time=current_time,
		end_time=current_time + datetime.timedelta(hours=config.RECLEAN_CYCLE_HOURS),
		duration_minutes=config.RECLEAN_CYCLE_HOURS * 60,
		notes='Initial line reclean'
	))
	current_time += datetime.timedelta(hours=config.RECLEAN_CYCLE_HOURS)
	total_changeover = 0
	total_reclean = 0
	run_time = 0
	hours_since_reclean = 0
	first_group = True

	for group_idx, t in enumerate(group_order):
		lots_in_group = type_groups[t]
		for i, lot in enumerate(lots_in_group):
			# Insert reclean if needed
			if (group_idx == 0 and i == 0) or hours_since_reclean >= config.MAX_CONTINUOUS_RUN_HOURS:
				schedule.append(ScheduleEntry(
					event_type='reclean',
					start_time=current_time,
					end_time=current_time + datetime.timedelta(hours=config.RECLEAN_CYCLE_HOURS),
					duration_minutes=config.RECLEAN_CYCLE_HOURS * 60,
					notes='Line reclean'
				))
				current_time += datetime.timedelta(hours=config.RECLEAN_CYCLE_HOURS)
				total_reclean += config.RECLEAN_CYCLE_HOURS * 60
				hours_since_reclean = 0

			# Insert changeover if needed
			if not (group_idx == 0 and i == 0):
				if i == 0:  # between groups
					changeover = config.CHANGEOVER_DIFF_TYPE_HOURS
				else:  # within group
					changeover = config.CHANGEOVER_SAME_TYPE_HOURS
				schedule.append(ScheduleEntry(
					event_type='changeover',
					lot_type=lot.type,
					start_time=current_time,
					end_time=current_time + datetime.timedelta(hours=changeover),
					duration_minutes=changeover * 60,
					notes=f'Changeover to {lot.type}'
				))
				current_time += datetime.timedelta(hours=changeover)
				total_changeover += changeover * 60
				hours_since_reclean += changeover

			# Fill lot
			fill_minutes = lot.vials / config.FILLING_RATE_VIALS_PER_MIN
			schedule.append(ScheduleEntry(
				event_type='fill',
				lot_id=lot.id,
				lot_type=lot.type,
				start_time=current_time,
				end_time=current_time + datetime.timedelta(minutes=fill_minutes),
				duration_minutes=fill_minutes,
				notes=f'Filling lot {lot.id}'
			))
			current_time += datetime.timedelta(minutes=fill_minutes)
			run_time += fill_minutes
			hours_since_reclean += fill_minutes / 60

	total_time = (current_time - now).total_seconds() / 60
	metrics = {
		'Total Time (min)': total_time,
		'Total Changeover Time (min)': total_changeover,
		'Total Reclean Time (min)': total_reclean,
		'Total Fill Time (min)': run_time
	}
	return schedule, metrics
