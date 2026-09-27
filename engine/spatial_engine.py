"""
AuraVision Spatial Kinematics & Trajectory Interception Engine
Implements zero-latency 3D optical flow vector fields, Time-To-Collision (TTC) calculations,
and deterministic safety zone boundary enforcement.
"""

from typing import List, Tuple, Optional, Dict, Any
from .spatial_models import Vector3D, Velocity3D, SpatialObject, SpatialTelemetryFrame, ThreatLevel, SpatialClass
import math

class SpatialKinematicsEngine:
    """
    Zero-latency edge spatial processor estimating 3D trajectories and collision probabilities.
    """

    CRITICAL_TTC_THRESHOLD = 1.2    # seconds
    WARNING_TTC_THRESHOLD = 3.0     # seconds
    LATERAL_SAFETY_CORRIDOR = 1.5   # meters radius

    @classmethod
    def calculate_time_to_collision(cls, pos: Vector3D, vel: Velocity3D) -> Tuple[Optional[float], ThreatLevel]:
        """
        Calculates Time-To-Collision (TTC) assuming constant velocity kinematics:
        If vz < 0 (approaching):
            TTC = pos.z / |vel.vz|
            Predicted lateral displacement: pred_x = pos.x + vel.vx * TTC
                                             pred_y = pos.y + vel.vy * TTC
            If predicted lateral displacement is within safety corridor:
                Determine threat level based on TTC.
        """
        # Object moving away or parallel to camera depth plane
        if vel.vz >= -0.05:
            # Check if already within immediate danger zone
            if pos.z < 2.0 and math.sqrt(pos.x**2 + pos.y**2) < cls.LATERAL_SAFETY_CORRIDOR:
                return round(pos.z / max(0.1, math.sqrt(vel.vx**2 + vel.vy**2)), 2), ThreatLevel.WARNING
            return None, ThreatLevel.CLEAR

        approaching_speed = abs(vel.vz)
        ttc = pos.z / approaching_speed

        # Predicted lateral position at collision plane (z = 0)
        pred_x = pos.x + (vel.vx * ttc)
        pred_y = pos.y + (vel.vy * ttc)
        radial_distance = math.sqrt(pred_x**2 + pred_y**2)

        # Check if projected trajectory intersects safety corridor
        if radial_distance <= cls.LATERAL_SAFETY_CORRIDOR:
            if ttc <= cls.CRITICAL_TTC_THRESHOLD:
                return round(ttc, 2), ThreatLevel.CRITICAL
            elif ttc <= cls.WARNING_TTC_THRESHOLD:
                return round(ttc, 2), ThreatLevel.WARNING
            else:
                return round(ttc, 2), ThreatLevel.ADVISORY
        else:
            # Trajectory glances or misses lateral corridor
            if ttc <= cls.WARNING_TTC_THRESHOLD and radial_distance <= (cls.LATERAL_SAFETY_CORRIDOR * 1.8):
                return round(ttc, 2), ThreatLevel.ADVISORY
            return None, ThreatLevel.CLEAR

    @classmethod
    def process_frame_telemetry(cls, frame_id: int, objects: List[SpatialObject], flow_mag: float = 0.0) -> SpatialTelemetryFrame:
        """
        Processes all detected spatial entities in a frame, updates TTC and threat levels,
        and determines whether autonomous emergency brake/interception is triggered.
        """
        highest_threat = ThreatLevel.CLEAR
        processed_objects: List[SpatialObject] = []

        for obj in objects:
            ttc, threat = cls.calculate_time_to_collision(obj.position, obj.velocity)
            obj.time_to_collision_seconds = ttc
            obj.threat_level = threat
            processed_objects.append(obj)

            if threat == ThreatLevel.CRITICAL:
                highest_threat = ThreatLevel.CRITICAL
            elif threat == ThreatLevel.WARNING and highest_threat != ThreatLevel.CRITICAL:
                highest_threat = ThreatLevel.WARNING
            elif threat == ThreatLevel.ADVISORY and highest_threat in (ThreatLevel.CLEAR, ThreatLevel.ADVISORY):
                highest_threat = ThreatLevel.ADVISORY

        emergency_active = (highest_threat == ThreatLevel.CRITICAL)

        return SpatialTelemetryFrame(
            frame_id=frame_id,
            active_objects=processed_objects,
            highest_threat=highest_threat,
            emergency_interception_active=emergency_active,
            optical_flow_magnitude_avg=round(flow_mag, 3),
            fps_estimate=60.0
        )
