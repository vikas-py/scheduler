"""
model_comparison_viz.py
Visualizes and compares the activity schedules of all models using Gantt charts.
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from filling_schedule_optimizer.strategies import fifo, spt_only, hybrid_heuristic, batch_binpack
from filling_schedule_optimizer import models, config
from datetime import datetime

# --- Load input data ---
data_path = os.path.join(os.path.dirname(__file__), 'data', 'example_lots.csv')
lots_df = pd.read_csv(data_path)

def lots_from_df(df):
    return [models.Lot(id=row["Lot ID"], type=row["Type"], vials=int(row["Vials"])) for _, row in df.iterrows()]

lots = lots_from_df(lots_df)

# --- Prepare strategies ---
strategies = [
    ("FIFO", fifo.generate_schedule),
    ("SPT Only", spt_only.generate_schedule),
    ("Hybrid Heuristic", hybrid_heuristic.generate_schedule),
    ("Batch BinPack", batch_binpack.batch_binpack_schedule),
]


# --- Collect schedule and KPI data for all models ---
model_schedules = []
kpi_rows = []

def compute_kpis(schedule, lots):
    fills = [e for e in schedule if getattr(e, "event_type", "").lower() == "fill"]
    changeovers = [e for e in schedule if getattr(e, "event_type", "").lower() == "changeover"]
    recleans = [e for e in schedule if getattr(e, "event_type", "").lower() == "reclean"]
    start_times = [e.start_time for e in schedule if getattr(e, "start_time", None)]
    end_times = [e.end_time for e in schedule if getattr(e, "end_time", None)]
    first_start = min(start_times) if start_times else None
    last_end = max(end_times) if end_times else None
    makespan = (last_end - first_start).total_seconds() / 60 if first_start and last_end else None
    total_changeover = sum(e.duration_minutes or 0 for e in changeovers)
    avg_changeover = (total_changeover / len(changeovers)) if changeovers else 0
    num_changeovers = len(changeovers)
    total_cleaning = sum(e.duration_minutes or 0 for e in recleans)
    return {
        "Total Makespan (min)": round(makespan, 2) if makespan else None,
        "Avg. Changeover Time (min)": round(avg_changeover, 2),
        "Number of Changeovers": num_changeovers,
        "Total Cleaning Time (min)": round(total_cleaning, 2),
    }

for name, strategy_func in strategies:
    try:
        schedule, _ = strategy_func(lots, config)
        # Convert to DataFrame for plotting
        rows = []
        for e in schedule:
            rows.append({
                'Model': name,
                'Event': getattr(e, 'event_type', ''),
                'Lot ID': getattr(e, 'lot_id', ''),
                'Start': getattr(e, 'start_time', None),
                'End': getattr(e, 'end_time', None),
                'Duration': getattr(e, 'duration_minutes', 0),
                'Lot Type': getattr(e, 'lot_type', ''),
            })
        model_schedules.append(pd.DataFrame(rows))
        kpi = compute_kpis(schedule, lots)
        kpi['Strategy'] = name
        kpi_rows.append(kpi)
    except Exception as ex:
        print(f"Error for {name}: {ex}")

# --- Combine all schedules ---
all_sched = pd.concat(model_schedules, ignore_index=True)

# --- Plotting ---
activity_colors = {'fill': '#4CAF50', 'changeover': '#FFC107', 'reclean': '#2196F3'}
activity_labels = {'fill': 'Fill', 'changeover': 'Changeover', 'reclean': 'Reclean'}

fig, axes = plt.subplots(len(strategies), 1, figsize=(14, 2.5 * len(strategies)), sharex=True)
if len(strategies) == 1:
    axes = [axes]

for idx, (name, _) in enumerate(strategies):
    ax = axes[idx]
    sched = all_sched[all_sched['Model'] == name]
    for _, row in sched.iterrows():
        color = activity_colors.get(row['Event'].lower(), '#BDBDBD')
        label = activity_labels.get(row['Event'].lower(), row['Event'])
        ax.barh(
            y=label,
            width=(row['End'] - row['Start']).total_seconds() / 3600 if row['End'] and row['Start'] else 0,
            left=(row['Start'] - sched['Start'].min()).total_seconds() / 3600 if row['Start'] else 0,
            height=0.6,
            color=color,
            edgecolor='black',
            alpha=0.8
        )
    ax.set_title(f"{name} Schedule")
    ax.set_ylabel("Activity")
    ax.grid(axis='x', linestyle='--', alpha=0.5)

axes[-1].set_xlabel("Hours from Schedule Start")

# Legend
patches = [mpatches.Patch(color=activity_colors[k], label=activity_labels[k]) for k in activity_colors]
plt.legend(handles=patches, bbox_to_anchor=(1.01, 1), loc='upper left')
plt.tight_layout(rect=[0, 0, 0.85, 1])

# --- Plotting (Gantt chart) ---
import itertools
activity_colors = {'changeover': '#FFC107', 'reclean': '#2196F3'}
activity_labels = {'fill': 'Fill', 'changeover': 'Changeover', 'reclean': 'Reclean'}

# Assign a unique color to each vial type for fill events
fill_types = sorted(all_sched[all_sched['Event'].str.lower() == 'fill']['Lot Type'].unique())
import matplotlib
fill_palette = matplotlib.colormaps.get_cmap('tab10')
fill_type_colors = {vtype: fill_palette(i % 10) for i, vtype in enumerate(fill_types)}

fig, axes = plt.subplots(len(strategies), 1, figsize=(14, 2.5 * len(strategies)), sharex=True)
if len(strategies) == 1:
    axes = [axes]

for idx, (name, _) in enumerate(strategies):
    ax = axes[idx]
    sched = all_sched[all_sched['Model'] == name]
    for _, row in sched.iterrows():
        event = row['Event'].lower()
        if event == 'fill':
            color = fill_type_colors.get(row['Lot Type'], '#4CAF50')
            label = f"Fill ({row['Lot Type']})"
        else:
            color = activity_colors.get(event, '#BDBDBD')
            label = activity_labels.get(event, row['Event'])
        ax.barh(
            y=label,
            width=(row['End'] - row['Start']).total_seconds() / 3600 if row['End'] and row['Start'] else 0,
            left=(row['Start'] - sched['Start'].min()).total_seconds() / 3600 if row['Start'] else 0,
            height=0.6,
            color=color,
            edgecolor='black',
            alpha=0.8
        )
    ax.set_title(f"{name} Schedule")
    ax.set_ylabel("Activity")
    ax.grid(axis='x', linestyle='--', alpha=0.5)

axes[-1].set_xlabel("Hours from Schedule Start")

# Legend: fill types and event types
patches = [mpatches.Patch(color=fill_type_colors[vtype], label=f'Fill ({vtype})') for vtype in fill_types]
patches += [mpatches.Patch(color=activity_colors[k], label=activity_labels[k]) for k in activity_colors]
plt.legend(handles=patches, bbox_to_anchor=(1.01, 1), loc='upper left')
plt.tight_layout(rect=[0, 0, 0.85, 1])


# Save Gantt chart to base64 for HTML embedding
from io import BytesIO
import base64
buf = BytesIO()
plt.savefig(buf, format='png')
plt.close()
buf.seek(0)
gantt_base64 = base64.b64encode(buf.read()).decode('utf-8')

# --- Build HTML report ---
html = [
    "<html>",
    "<head>",
    "<title>Model Comparison Report</title>",
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
    "<h1>Model Comparison Report</h1>",
    "<h2>Schedule Gantt Chart</h2>",
    f'<img src="data:image/png;base64,{gantt_base64}" style="max-width:1000px; width:100%; border:1px solid #ccc;"/>'
]

# KPI Table
if kpi_rows:
    html.append("<h2>Key Performance Indicators (KPIs)</h2>")
    df_kpi = pd.DataFrame(kpi_rows)
    html.append("<table>")
    html.append("<tr>" + "".join(f"<th>{col}</th>" for col in df_kpi.columns) + "</tr>")
    for _, row in df_kpi.iterrows():
        html.append("<tr>" + "".join(f"<td>{row[col]}</td>" for col in df_kpi.columns) + "</tr>")
    html.append("</table>")


# Add detailed schedule tables for each model
for idx, (name, _) in enumerate(strategies):
    sched = model_schedules[idx]
    html.append(f"<h2>Schedule Details: {name}</h2>")
    html.append("<table>")
    html.append("<tr>" + "".join(f"<th>{col}</th>" for col in sched.columns) + "</tr>")
    for _, row in sched.iterrows():
        html.append("<tr>" + "".join(f"<td>{row[col]}</td>" for col in sched.columns) + "</tr>")
    html.append("</table>")

html.append(f"<p>Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>")
html.append("</body></html>")

# Save HTML report
output_path = os.path.join(os.path.dirname(__file__), 'reports', 'model_comparison_report.html')
with open(output_path, 'w', encoding='utf-8') as f:
    f.write("\n".join(html))
print(f"Model comparison HTML report saved to {output_path}")
