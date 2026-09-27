"""
AuraVision Domain Models & Spatial Kinematics Types
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum
import time

class ThreatLevel(Enum):
    CLEAR = "CLEAR"           # Safe operational corridor
    ADVISORY = "ADVISORY"     # Distant object entering perimeter
    WARNING = "WARNING"       # Trajectory crossing safety zone (< 3.0s TTC)
    CRITICAL = "CRITICAL"     # Imminent collision / emergency braking (< 1.2s TTC)

class SpatialClass(Enum):
    HUMAN_OPERATOR = "Human Operator"
    AUTONOMOUS_VEHICLE = "Autonomous Vehicle / Forklift"
    STATIC_OBSTACLE = "Static Infrastructure"
    HIGH_SPEED_PROJECTILE = "High-Speed Dynamic Object"
    UNKNOWN_DYNAMIC = "Unknown Dynamic Entity"

@dataclass
class Vector3D:
    x: float  # Horizontal offset from camera center (meters, +Right)
    y: float  # Vertical offset from camera center (meters, +Up)
    z: float  # Depth from camera plane (meters, +Forward)

@dataclass
class Velocity3D:
    vx: float  # m/s (+Right)
    vy: float  # m/s (+Up)
    vz: float  # m/s (+Forward, negative means approaching camera)

@dataclass
class SpatialObject:
    object_id: str
    spatial_class: SpatialClass
    confidence: float
    position: Vector3D
    velocity: Velocity3D
    bounding_box: Tuple[int, int, int, int]  # (x, y, w, h) in pixels
    time_to_collision_seconds: Optional[float] = None
    threat_level: ThreatLevel = ThreatLevel.CLEAR
    timestamp: float = field(default_factory=time.time)

@dataclass
class SpatialTelemetryFrame:
    frame_id: int
    active_objects: List[SpatialObject]
    highest_threat: ThreatLevel
    emergency_interception_active: bool
    optical_flow_magnitude_avg: float
    fps_estimate: float
    timestamp: float = field(default_factory=time.time)
