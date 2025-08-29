# config.py
# Centralized configuration for the filling line scheduling tool

# Filling line parameters
FILLING_RATE_VIALS_PER_MIN = 332
CHANGEOVER_SAME_TYPE_HOURS = 4
CHANGEOVER_DIFF_TYPE_HOURS = 8
RECLEAN_CYCLE_HOURS = 24
MAX_CONTINUOUS_RUN_HOURS = 120

# --- Batch/Bin-Packing Strategy Settings ---
# Maximum allowed time (in hours) for a clean window/bin before reclean is required
BATCH_BINPACK_CLEAN_WINDOW_HOURS = 120
# Enable local search improvement (swap lots to reduce changeover)
BATCH_BINPACK_LOCAL_SEARCH = True
# Enable clustering of small lots after type changeover
BATCH_BINPACK_CLUSTER_SMALL_LOTS = True
# Minimum lot size (vials) to consider as 'small' for clustering
BATCH_BINPACK_SMALL_LOT_THRESHOLD = 50000

# File paths
DATA_FILE = "filling_schedule_optimizer/data/example_lots.csv"
REPORT_FILE = "filling_schedule_optimizer/reports/schedule_report.html"

# Scheduling strategy: 'hybrid_heuristic', 'spt_only', or 'fifo'
SCHEDULING_STRATEGY = "spt_only"

# Schedule start datetime (ISO format: 'YYYY-MM-DD HH:MM')
# If None, uses current datetime
SCHEDULE_START_DATETIME = '2025-09-01 08:00'  # e.g., '2025-09-01 08:00'
