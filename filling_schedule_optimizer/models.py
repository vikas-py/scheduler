# models.py
# Data models for the filling line scheduling tool

from dataclasses import dataclass
from typing import Optional
import datetime

@dataclass
class Lot:
	id: str
	type: str
	vials: int
	description: Optional[str] = None  # Not required in CSV

@dataclass
class ScheduleEntry:
	event_type: str  # 'fill', 'changeover', 'reclean'
	lot_id: Optional[str] = None
	lot_type: Optional[str] = None
	start_time: Optional[datetime.datetime] = None
	end_time: Optional[datetime.datetime] = None
	duration_minutes: Optional[int] = None
	notes: Optional[str] = None
