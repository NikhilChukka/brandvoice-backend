# app/models/enums.py
from enum import Enum

class Platform(str, Enum):
    instagram = "instagram"
    linkedin  = "linkedin"
    x         = "x"

class ScheduleState(str, Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"
