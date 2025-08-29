# validation.py
# Data validation for lots input

from typing import List
from .models import Lot

def validate_lots(lots: List[Lot]) -> List[str]:
	"""
	Validates a list of Lot objects.
	Returns a list of error messages (empty if valid).
	"""
	errors = []
	seen_ids = set()
	for i, lot in enumerate(lots):
		if not lot.id:
			errors.append(f"Lot at index {i} is missing an ID.")
		if not lot.type:
			errors.append(f"Lot {lot.id or i} is missing a type.")
		if not isinstance(lot.vials, int) or lot.vials <= 0:
			errors.append(f"Lot {lot.id or i} has invalid vials: {lot.vials}.")
		if lot.id in seen_ids:
			errors.append(f"Duplicate Lot ID found: {lot.id}.")
		seen_ids.add(lot.id)
	return errors
