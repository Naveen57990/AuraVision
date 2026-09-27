#!/usr/bin/env python3
"""
AuraVision Tactical Spatial Radar CLI
Edge Computer Vision & 3D Kinematic Hazard Interceptor
"""

import sys
import os
import argparse
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.spatial_models import Vector3D, Velocity3D, SpatialObject, ThreatLevel, SpatialClass
from engine.spatial_engine import SpatialKinematicsEngine
from engine.aws_edge_sync import AWSIoTEdgeDispatcher

# ANSI Colors
RED = "\033[1;31m"
ORANGE = "\033[1;33m"
YELLOW = "\033[0;33m"
GREEN = "\033[1;32m"
CYAN = "\033[1;36m"
WHITE = "\033[1;37m"
GRAY = "\033[0;90m"
RESET = "\033[0m"
BOLD = "\033[1m"

def get_threat_badge(threat: ThreatLevel) -> str:
    if threat == ThreatLevel.CRITICAL:
        return f"{RED}[ CRITICAL COLLISION THREAT - EMERGENCY BRAKE ]{RESET}"
    elif threat == ThreatLevel.WARNING:
        return f"{ORANGE}[ WARNING - HAZARD IN BOUNDARY (<3.0s TTC) ]{RESET}"
    elif threat == ThreatLevel.ADVISORY:
        return f"{YELLOW}[ ADVISORY - DISTANT CONE INTERSECTION ]{RESET}"
    else:
        return f"{GREEN}[ OPERATIONAL CORRIDOR CLEAR ]{RESET}"

def print_spatial_radar_card(frame):
    badge = get_threat_badge(frame.highest_threat)
    print(f"\n{CYAN}{'='*68}{RESET}")
    print(f"{BOLD}AURAVISION SPATIAL RADAR & KINEMATIC FRAME #{frame.frame_id}{RESET} | Status: {badge}")
    print(f"{CYAN}{'='*68}{RESET}")
    print(f"{BOLD}Telemetry:{RESET} Tracked Entities: {len(frame.active_objects)} | Est FPS: {frame.fps_estimate:.0f} | Flow Mag: {frame.optical_flow_magnitude_avg:.2f} px/f")
    print(f"{BOLD}AWS IoT Core Edge Sync:{RESET} {'EMERGENCY MQTT DISPATCH (QoS 1)' if frame.emergency_interception_active else 'ROUTINE TELEMETRY (QoS 0)'}")
    
    print(f"\n{GRAY}--- 3D SPATIAL KINEMATIC TRACKING MATRIX ---{RESET}")
    print(f"{'ID':<12} | {'Class':<22} | {'Pos (X,Y,Z) m':<16} | {'Vel (Vx,Vy,Vz)':<16} | {'TTC (s)':<8} | {'Threat'}")
    print(f"{'-'*90}")

    for obj in frame.active_objects:
        pos_str = f"({obj.position.x:.1f}, {obj.position.y:.1f}, {obj.position.z:.1f})"
        vel_str = f"({obj.velocity.vx:.1f}, {obj.velocity.vy:.1f}, {obj.velocity.vz:.1f})"
        ttc_str = f"{obj.time_to_collision_seconds:.2f}s" if obj.time_to_collision_seconds else "--"
        
        t_color = RED if obj.threat_level == ThreatLevel.CRITICAL else (ORANGE if obj.threat_level == ThreatLevel.WARNING else (YELLOW if obj.threat_level == ThreatLevel.ADVISORY else GREEN))
        
        print(f"{obj.object_id:<12} | {obj.spatial_class.value:<22} | {pos_str:<16} | {vel_str:<16} | {ttc_str:<8} | {t_color}{obj.threat_level.value}{RESET}")

    print(f"{CYAN}{'='*68}{RESET}\n")

def demo_simulation():
    print(f"{BOLD}{CYAN}Initializing AuraVision Edge Spatial Awareness Benchmark (Live Stream)...{RESET}")
    
    scenarios = [
        # Frame 1: Clear
        [
            SpatialObject("PED_01", SpatialClass.HUMAN_OPERATOR, 0.95, Vector3D(4.0, 0.0, 20.0), Velocity3D(0.5, 0.0, -1.0), (100, 200, 40, 90)),
            SpatialObject("AGV_02", SpatialClass.AUTONOMOUS_VEHICLE, 0.98, Vector3D(-5.0, 0.0, 30.0), Velocity3D(-1.0, 0.0, 2.0), (400, 180, 80, 60))
        ],
        # Frame 2: Warning
        [
            SpatialObject("PED_01", SpatialClass.HUMAN_OPERATOR, 0.96, Vector3D(1.2, 0.0, 10.0), Velocity3D(-0.4, 0.0, -4.0), (220, 180, 60, 120)),
            SpatialObject("AGV_02", SpatialClass.AUTONOMOUS_VEHICLE, 0.99, Vector3D(-6.0, 0.0, 32.0), Velocity3D(-1.0, 0.0, 2.0), (420, 175, 75, 55))
        ],
        # Frame 3: Critical
        [
            SpatialObject("PED_01", SpatialClass.HUMAN_OPERATOR, 0.98, Vector3D(0.1, 0.0, 4.5), Velocity3D(-0.1, 0.0, -5.0), (300, 120, 120, 240)),
            SpatialObject("STATIC_03", SpatialClass.STATIC_OBSTACLE, 0.99, Vector3D(2.5, 0.0, 8.0), Velocity3D(0.0, 0.0, 0.0), (500, 220, 100, 100))
        ]
    ]

    for idx, objects in enumerate(scenarios):
        frame = SpatialKinematicsEngine.process_frame_telemetry(frame_id=idx+1, objects=objects, flow_mag=(idx+1)*1.8)
        event = AWSIoTEdgeDispatcher.dispatch_edge_event(frame)
        print_spatial_radar_card(frame)
        time.sleep(0.3)

def main():
    parser = argparse.ArgumentParser(description="AuraVision Spatial Radar & Edge Kinematics CLI")
    parser.add_argument("--demo", action="store_true", help="Run 3D kinematic tracking benchmark simulation")
    parser.add_argument("--x", type=float, default=0.0, help="Object X lateral position (m)")
    parser.add_argument("--y", type=float, default=0.0, help="Object Y vertical position (m)")
    parser.add_argument("--z", type=float, default=6.0, help="Object Z depth distance (m)")
    parser.add_argument("--vx", type=float, default=0.0, help="Object lateral velocity Vx (m/s)")
    parser.add_argument("--vy", type=float, default=0.0, help="Object vertical velocity Vy (m/s)")
    parser.add_argument("--vz", type=float, default=-5.0, help="Object approaching depth velocity Vz (m/s)")

    args = parser.parse_args()

    if args.demo:
        demo_simulation()
        return

    obj = SpatialObject(
        object_id="PROBE_01",
        spatial_class=SpatialClass.HUMAN_OPERATOR,
        confidence=0.97,
        position=Vector3D(args.x, args.y, args.z),
        velocity=Velocity3D(args.vx, args.vy, args.vz),
        bounding_box=(200, 150, 100, 200)
    )
    frame = SpatialKinematicsEngine.process_frame_telemetry(frame_id=1, objects=[obj], flow_mag=3.5)
    print_spatial_radar_card(frame)

if __name__ == "__main__":
    main()
