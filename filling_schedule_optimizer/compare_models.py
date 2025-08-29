"""
compare_models.py
Runs all scheduling strategies on the same input and compares their outputs.
"""

import os
import pandas as pd
from filling_schedule_optimizer.strategies import fifo, spt_only, hybrid_heuristic
from filling_schedule_optimizer import models, validation, config
from datetime import datetime

# --- Load input data ---
data_path = os.path.join(os.path.dirname(__file__), 'data', 'example_lots.csv')
lots_df = pd.read_csv(data_path)

# Convert DataFrame to List[Lot]
def lots_from_df(df):
    return [models.Lot(id=row["Lot ID"], type=row["Type"], vials=int(row["Vials"])) for _, row in df.iterrows()]

lots = lots_from_df(lots_df)

# --- Prepare strategies ---
strategies = [
    ("FIFO", fifo.generate_schedule),
    ("SPT Only", spt_only.generate_schedule),
    ("Hybrid Heuristic", hybrid_heuristic.generate_schedule),
]

def compute_kpis(schedule, metrics, lots):
    # Extract events
    fills = [e for e in schedule if getattr(e, "event_type", "").lower() == "fill"]
    changeovers = [e for e in schedule if getattr(e, "event_type", "").lower() == "changeover"]
    recleans = [e for e in schedule if getattr(e, "event_type", "").lower() == "reclean"]
    # Timespan
    start_times = [e.start_time for e in schedule if getattr(e, "start_time", None)]
    end_times = [e.end_time for e in schedule if getattr(e, "end_time", None)]
    first_start = min(start_times) if start_times else None
    last_end = max(end_times) if end_times else None
    makespan = (last_end - first_start).total_seconds() / 60 if first_start and last_end else None
    # Changeover
    total_changeover = sum(e.duration_minutes or 0 for e in changeovers)
    avg_changeover = (total_changeover / len(changeovers)) if changeovers else 0
    num_changeovers = len(changeovers)
    # Cleaning
    total_cleaning = sum(e.duration_minutes or 0 for e in recleans)    python3 -m filling_schedule_optimizer.compare_models
    return {
        "Total Makespan (min)": round(makespan, 2) if makespan else None,
        "Avg. Changeover Time (min)": round(avg_changeover, 2),
        "Number of Changeovers": num_changeovers,
        "Total Cleaning Time (min)": round(total_cleaning, 2),
    }

results = []
for name, strategy_func in strategies:
    try:
        schedule, metrics = strategy_func(lots, config)
        kpis = compute_kpis(schedule, metrics, lots)
        kpis["Strategy"] = name
        results.append(kpis)
    except Exception as e:
        results.append({"Strategy": name, "Error": str(e)})

# Print comparison table
df = pd.DataFrame(results)
cols = ["Strategy", "Total Makespan (min)", "Avg. Changeover Time (min)", "Number of Changeovers", "Total Cleaning Time (min)"]
print("\nModel Comparison Results:")
print(df[cols].to_string(index=False))
