"""
batch_binpack.py
Batch/bin-packing scheduling strategy with clean window, local search, and clustering improvements.
"""
from typing import List, Tuple, Dict
from ..models import Lot, ScheduleEntry
from .. import config
import datetime
import copy
from collections import defaultdict

def calculate_fill_time(lot):
    return lot.vials / config.FILLING_RATE_VIALS_PER_MIN

def calculate_changeover(prev_lot, lot):
    if prev_lot is None:
        return 0
    if prev_lot.type == lot.type:
        return config.CHANGEOVER_SAME_TYPE_HOURS
    else:
        return config.CHANGEOVER_DIFF_TYPE_HOURS

def batch_binpack_schedule(lots: List[Lot], config=config) -> Tuple[List[ScheduleEntry], Dict]:
    # 1. Group by type
    grouped = defaultdict(list)
    for lot in lots:
        grouped[lot.type].append(lot)
    # 2. Sort within each type (by size descending)
    for t in grouped:
        grouped[t].sort(key=lambda l: -l.vials)
    # 3. Clean window bin-packing
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

    # Prevent consecutive recleans: skip reclean if previous event is reclean
    clean_window_limit = config.BATCH_BINPACK_CLEAN_WINDOW_HOURS
    while any(grouped.values()):
        current_window = []
        current_window_time = 0
        previous_lot = None
        # Try to fill the window
        for t in list(grouped.keys()):
            lots_of_type = grouped[t]
            i = 0
            while i < len(lots_of_type):
                lot = lots_of_type[i]
                fill_time = calculate_fill_time(lot) / 60  # in hours
                changeover_time = calculate_changeover(previous_lot, lot)
                if current_window_time + fill_time + changeover_time <= clean_window_limit:
                    current_window.append((lot, changeover_time))
                    current_window_time += fill_time + changeover_time
                    previous_lot = lot
                    lots_of_type.pop(i)
                else:
                    i += 1
            if not lots_of_type:
                del grouped[t]
        # Schedule the window
        for idx, (lot, changeover_time) in enumerate(current_window):
            if idx == 0 and schedule:
                # Add changeover from previous window if needed
                prev_lot = schedule[-1].lot_id and schedule[-1].lot_type
                if prev_lot and lot.type != prev_lot:
                    schedule.append(ScheduleEntry(
                        event_type='changeover',
                        lot_type=lot.type,
                        start_time=current_time,
                        end_time=current_time + datetime.timedelta(hours=changeover_time),
                        duration_minutes=changeover_time * 60,
                        notes=f'Changeover to {lot.type}'
                    ))
                    current_time += datetime.timedelta(hours=changeover_time)
            elif changeover_time > 0:
                schedule.append(ScheduleEntry(
                    event_type='changeover',
                    lot_type=lot.type,
                    start_time=current_time,
                    end_time=current_time + datetime.timedelta(hours=changeover_time),
                    duration_minutes=changeover_time * 60,
                    notes=f'Changeover to {lot.type}'
                ))
                current_time += datetime.timedelta(hours=changeover_time)
            fill_minutes = calculate_fill_time(lot)
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
        # Add reclean at end of window only if there are lots remaining
        if any(grouped.values()):
            schedule.append(ScheduleEntry(
                event_type='reclean',
                start_time=current_time,
                end_time=current_time + datetime.timedelta(hours=config.RECLEAN_CYCLE_HOURS),
                duration_minutes=config.RECLEAN_CYCLE_HOURS * 60,
                notes='Line reclean'
            ))
            current_time += datetime.timedelta(hours=config.RECLEAN_CYCLE_HOURS)
    # 4. Local search and swap improvements (adjacent swaps)
    def objective(sched):
        # Minimize makespan, changeover, and reclean time
        makespan = (sched[-1].end_time - sched[0].start_time).total_seconds() / 60 if sched else 0
        changeover = sum(e.duration_minutes or 0 for e in sched if e.event_type == 'changeover')
        reclean = sum(e.duration_minutes or 0 for e in sched if e.event_type == 'reclean')
        return makespan + changeover + reclean

    # Only consider fill events for swapping
    fill_indices = [i for i, e in enumerate(schedule) if e.event_type == 'fill']
    improved = True
    while improved:
        improved = False
        for idx in range(len(fill_indices) - 1):
            i, j = fill_indices[idx], fill_indices[idx + 1]
            # Swap two adjacent fills and rebuild the schedule window if it improves objective
            new_schedule = schedule[:]
            new_schedule[i], new_schedule[j] = new_schedule[j], new_schedule[i]
            if objective(new_schedule) < objective(schedule):
                schedule = new_schedule
                improved = True
                break  # Restart after improvement
        if improved:
            # Recompute fill_indices after a swap
            fill_indices = [i for i, e in enumerate(schedule) if e.event_type == 'fill']

    # 5. Clustering small lots after type changeover
    # Move small lots of the same type after a type changeover together
    clustered_schedule = []
    i = 0
    while i < len(schedule):
        e = schedule[i]
        clustered_schedule.append(e)
        if e.event_type == 'changeover':
            # Find small lots of the same type immediately after changeover
            j = i + 1
            small_lots = []
            while j < len(schedule) and schedule[j].event_type == 'fill' and schedule[j].lot_type == e.lot_type and schedule[j].duration_minutes <= config.BATCH_BINPACK_SMALL_LOT_THRESHOLD / config.FILLING_RATE_VIALS_PER_MIN:
                small_lots.append(schedule[j])
                j += 1
            # Sort small lots by size ascending (optional)
            small_lots.sort(key=lambda x: x.duration_minutes)
            clustered_schedule.extend(small_lots)
            i = j - 1 + len(small_lots)
        i += 1
    schedule = clustered_schedule

    # Metrics
    start_time = schedule[0].start_time if schedule else now
    end_time = schedule[-1].end_time if schedule else now
    total_time = (end_time - start_time).total_seconds() / 60
    total_changeover = sum(e.duration_minutes or 0 for e in schedule if e.event_type == 'changeover')
    total_reclean = sum(e.duration_minutes or 0 for e in schedule if e.event_type == 'reclean')
    run_time = sum(e.duration_minutes or 0 for e in schedule if e.event_type == 'fill')
    metrics = {
        'Total Time (min)': total_time,
        'Total Changeover Time (min)': total_changeover,
        'Total Reclean Time (min)': total_reclean,
        'Total Fill Time (min)': run_time
    }
    return schedule, metrics
