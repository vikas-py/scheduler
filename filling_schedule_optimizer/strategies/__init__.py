# Explicitly import all strategy modules for package initialization
from .fifo import generate_schedule as fifo_schedule
from .spt_only import generate_schedule as spt_only_schedule
from .hybrid_heuristic import generate_schedule as hybrid_heuristic_schedule
from .batch_binpack import batch_binpack_schedule
