# config.py
# Centralized configuration for the filling line scheduling tool

# Filling line parameters
FILLING_RATE_VIALS_PER_MIN = 332
CHANGEOVER_SAME_TYPE_HOURS = 4
CHANGEOVER_DIFF_TYPE_HOURS = 8
RECLEAN_CYCLE_HOURS = 24
MAX_CONTINUOUS_RUN_HOURS = 120

# File paths
DATA_FILE = "filling_schedule_optimizer/data/example_lots.csv"
REPORT_FILE = "filling_schedule_optimizer/reports/schedule_report.html"

# Scheduling strategy: 'hybrid_heuristic', 'spt_only', or 'fifo'
SCHEDULING_STRATEGY = "hybrid_heuristic"
