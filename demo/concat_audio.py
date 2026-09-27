#!/usr/bin/env python3
"""
Measure scene durations and concatenate into a single audio file with exact scene timestamp metadata for AuraVision.
"""

import os
import json
import subprocess

DEMO_DIR = os.path.dirname(os.path.abspath(__file__))

SCENES = [
    {"id": "scene1_intro", "text": "In modern smart factories and collaborative robotic spaces, autonomous mobile robots and humans share tight physical corridors. Traditional cloud computer vision is too slow for critical collision avoidance. Introducing AuraVision: an edge-native spatial awareness engine powered by OpenCV 5 and AWS IoT."},
    {"id": "scene2_opencv_spatial", "text": "AuraVision calculates dense optical flow vector fields at sixty frames per second directly on the edge. By projecting three-dimensional bounding frustums and kinematic velocity vectors, AuraVision continuously monitors the operational safety envelope in real time."},
    {"id": "scene3_ttc_interception", "text": "Here, when a worker enters the path of an automated guided vehicle, AuraVision computes the exact Time-To-Collision. As the trajectory crosses the lateral safety corridor with a sub-one-point-two second threshold, AuraVision instantly triggers an emergency braking interception."},
    {"id": "scene4_aws_greengrass", "text": "Simultaneously, AuraVision synchronizes high-priority hazard events to AWS IoT Greengrass with guaranteed Quality of Service over lightweight MQTT topics, ensuring full cloud observability without incurring high-latency round-trip bottlenecks."},
    {"id": "scene5_cli_closing", "text": "With full multi-entity swarm tracking and a deterministic terminal CLI, AuraVision delivers sub-four-millisecond spatial intelligence. Open source, robust, and engineered for next-generation physical AI safety."}
]

def get_duration(file_path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    out = subprocess.check_output(cmd).decode().strip()
    return float(out)

def main():
    concat_list = os.path.join(DEMO_DIR, "concat_list.txt")
    with open(concat_list, "w") as f:
        for s in SCENES:
            mp3_name = f"{s['id']}.mp3"
            f.write(f"file '{mp3_name}'\n")

    output_audio = os.path.join(DEMO_DIR, "auravision_full_narration.mp3")
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-c", "copy", output_audio
    ]
    subprocess.run(cmd, check=True)

    current_time = 0.0
    timeline = []
    for s in SCENES:
        dur = get_duration(os.path.join(DEMO_DIR, f"{s['id']}.mp3"))
        start = current_time
        end = current_time + dur
        current_time = end
        timeline.append({
            "id": s["id"],
            "text": s["text"],
            "start": round(start, 2),
            "end": round(end, 2),
            "duration": round(dur, 2)
        })

    print("Total Audio Duration:", current_time)
    print("Timeline:", json.dumps(timeline, indent=2))

    with open(os.path.join(DEMO_DIR, "timeline.json"), "w") as f:
        json.dump({"total_duration": current_time, "scenes": timeline}, f, indent=2)

if __name__ == "__main__":
    main()
