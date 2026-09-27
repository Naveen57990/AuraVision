"""
AuraVision Comprehensive Deterministic Unit Test Suite
Validates 3D spatial velocity estimation, optical flow kinematics, Time-To-Collision (TTC),
lateral safety corridors, and AWS IoT Greengrass edge payload formatting.
"""

import unittest
from .spatial_models import Vector3D, Velocity3D, SpatialObject, ThreatLevel, SpatialClass
from .spatial_engine import SpatialKinematicsEngine
from .aws_edge_sync import AWSIoTEdgeDispatcher

class TestAuraVisionEngine(unittest.TestCase):

    def test_imminent_head_on_collision_critical_ttc(self):
        # Object 6 meters away, moving towards camera at 6 m/s (TTC = 1.0s <= 1.2s -> CRITICAL)
        pos = Vector3D(x=0.0, y=0.0, z=6.0)
        vel = Velocity3D(vx=0.0, vy=0.0, vz=-6.0)
        ttc, threat = SpatialKinematicsEngine.calculate_time_to_collision(pos, vel)
        self.assertEqual(threat, ThreatLevel.CRITICAL)
        self.assertAlmostEqual(ttc, 1.0, places=2)

    def test_moderate_approaching_warning_ttc(self):
        # Object 10 meters away, moving towards camera at 5 m/s (TTC = 2.0s <= 3.0s -> WARNING)
        pos = Vector3D(x=0.2, y=-0.1, z=10.0)
        vel = Velocity3D(vx=0.0, vy=0.0, vz=-5.0)
        ttc, threat = SpatialKinematicsEngine.calculate_time_to_collision(pos, vel)
        self.assertEqual(threat, ThreatLevel.WARNING)
        self.assertAlmostEqual(ttc, 2.0, places=2)

    def test_distant_approaching_advisory_ttc(self):
        # Object 25 meters away, moving towards camera at 5 m/s (TTC = 5.0s > 3.0s -> ADVISORY)
        pos = Vector3D(x=0.0, y=0.0, z=25.0)
        vel = Velocity3D(vx=0.0, vy=0.0, vz=-5.0)
        ttc, threat = SpatialKinematicsEngine.calculate_time_to_collision(pos, vel)
        self.assertEqual(threat, ThreatLevel.ADVISORY)
        self.assertAlmostEqual(ttc, 5.0, places=2)

    def test_receding_object_is_clear(self):
        # Object moving away from camera (vz = +4.0 m/s)
        pos = Vector3D(x=1.0, y=0.0, z=8.0)
        vel = Velocity3D(vx=0.0, vy=0.0, vz=4.0)
        ttc, threat = SpatialKinematicsEngine.calculate_time_to_collision(pos, vel)
        self.assertEqual(threat, ThreatLevel.CLEAR)
        self.assertIsNone(ttc)

    def test_divergent_trajectory_missing_lateral_corridor(self):
        # Object approaching in depth but steering far to the right (x = 5.0m, vx = +2.0m/s)
        pos = Vector3D(x=5.0, y=0.0, z=10.0)
        vel = Velocity3D(vx=2.0, vy=0.0, vz=-5.0)
        ttc, threat = SpatialKinematicsEngine.calculate_time_to_collision(pos, vel)
        self.assertEqual(threat, ThreatLevel.CLEAR)

    def test_multi_object_frame_telemetry_aggregation(self):
        obj1 = SpatialObject(
            object_id="HUMAN_01",
            spatial_class=SpatialClass.HUMAN_OPERATOR,
            confidence=0.96,
            position=Vector3D(x=0.0, y=0.0, z=5.0),
            velocity=Velocity3D(vx=0.0, vy=0.0, vz=-5.0), # TTC = 1.0s -> CRITICAL
            bounding_box=(200, 150, 80, 180)
        )
        obj2 = SpatialObject(
            object_id="FORKLIFT_02",
            spatial_class=SpatialClass.AUTONOMOUS_VEHICLE,
            confidence=0.91,
            position=Vector3D(x=3.0, y=0.0, z=15.0),
            velocity=Velocity3D(vx=0.0, vy=0.0, vz=0.0), # Static
            bounding_box=(400, 200, 120, 100)
        )
        frame = SpatialKinematicsEngine.process_frame_telemetry(frame_id=101, objects=[obj1, obj2], flow_mag=4.25)
        self.assertEqual(frame.highest_threat, ThreatLevel.CRITICAL)
        self.assertTrue(frame.emergency_interception_active)
        self.assertEqual(len(frame.active_objects), 2)
        self.assertEqual(frame.active_objects[0].threat_level, ThreatLevel.CRITICAL)

    def test_aws_iot_edge_dispatcher_serialization(self):
        obj = SpatialObject(
            object_id="AGV_04",
            spatial_class=SpatialClass.AUTONOMOUS_VEHICLE,
            confidence=0.98,
            position=Vector3D(x=0.0, y=0.0, z=4.0),
            velocity=Velocity3D(vx=0.0, vy=0.0, vz=-4.0),
            bounding_box=(300, 200, 100, 100)
        )
        frame = SpatialKinematicsEngine.process_frame_telemetry(frame_id=202, objects=[obj], flow_mag=2.1)
        event = AWSIoTEdgeDispatcher.dispatch_edge_event(frame)
        self.assertEqual(event["status"], "PUBLISHED_AWS_IOT")
        self.assertEqual(event["topic"], AWSIoTEdgeDispatcher.TOPIC_HAZARD_ALERTS)
        self.assertEqual(event["qos"], 1)
        self.assertEqual(event["payload"]["highest_threat"], "CRITICAL")
        self.assertTrue(event["payload"]["emergency_brake_triggered"])

    def test_stationary_proximity_warning(self):
        # Object very close (z = 1.5m, lateral = 0.5m) with minimal velocity
        pos = Vector3D(x=0.5, y=0.0, z=1.5)
        vel = Velocity3D(vx=0.0, vy=0.0, vz=0.0)
        ttc, threat = SpatialKinematicsEngine.calculate_time_to_collision(pos, vel)
        self.assertEqual(threat, ThreatLevel.WARNING)

if __name__ == "__main__":
    unittest.main()
