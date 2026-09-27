"""
AuraVision AWS Edge Telemetry & IoT Core Dispatcher
Simulates low-latency binary edge synchronization with AWS IoT Greengrass and Amazon Kinesis Video Streams.
"""

import json
import time
from typing import Dict, Any, List
from .spatial_models import SpatialTelemetryFrame, ThreatLevel

class AWSIoTEdgeDispatcher:
    """
    Dispatches critical spatial event notifications and telemetry batches to AWS IoT Greengrass topics.
    """

    TOPIC_HAZARD_ALERTS = "auravision/edge/hazards/critical"
    TOPIC_TELEMETRY_STREAM = "auravision/edge/telemetry/stream"

    @classmethod
    def serialize_telemetry_frame(cls, frame: SpatialTelemetryFrame) -> Dict[str, Any]:
        """Encodes frame into lightweight JSON payload for low-bandwidth cellular/satellite edge uplinks."""
        payload = {
            "frame_id": frame.frame_id,
            "timestamp_ms": int(frame.timestamp * 1000),
            "highest_threat": frame.highest_threat.value,
            "emergency_brake_triggered": frame.emergency_interception_active,
            "flow_magnitude": frame.optical_flow_magnitude_avg,
            "fps": frame.fps_estimate,
            "tracked_objects_count": len(frame.active_objects),
            "objects": [
                {
                    "id": obj.object_id,
                    "class": obj.spatial_class.value,
                    "confidence": round(obj.confidence, 2),
                    "pos": {"x": round(obj.position.x, 2), "y": round(obj.position.y, 2), "z": round(obj.position.z, 2)},
                    "vel": {"vx": round(obj.velocity.vx, 2), "vy": round(obj.velocity.vy, 2), "vz": round(obj.velocity.vz, 2)},
                    "ttc_sec": obj.time_to_collision_seconds,
                    "threat": obj.threat_level.value
                }
                for obj in frame.active_objects
            ]
        }
        return payload

    @classmethod
    def dispatch_edge_event(cls, frame: SpatialTelemetryFrame) -> Dict[str, Any]:
        """Simulates immediate MQTT publish to AWS IoT Core broker."""
        payload = cls.serialize_telemetry_frame(frame)
        topic = cls.TOPIC_HAZARD_ALERTS if frame.emergency_interception_active else cls.TOPIC_TELEMETRY_STREAM
        
        return {
            "status": "PUBLISHED_AWS_IOT",
            "topic": topic,
            "payload_bytes": len(json.dumps(payload)),
            "qos": 1 if frame.emergency_interception_active else 0,
            "payload": payload
        }
