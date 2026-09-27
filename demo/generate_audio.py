#!/usr/bin/env python3
"""
Generate high-fidelity voiceover narration for AuraVision demo video.
Uses edge-tts with en-US-AndrewNeural voice.
"""

import asyncio
import os
import edge_tts

VOICE = "en-US-AndrewNeural"
RATE = "-2%"
PITCH = "+0Hz"

SCENES = [
    {
        "id": "scene1_intro",
        "text": "In modern smart factories and collaborative robotic spaces, autonomous mobile robots and humans share tight physical corridors. Traditional cloud computer vision is too slow for critical collision avoidance. Introducing AuraVision: an edge-native spatial awareness engine powered by OpenCV 5 and AWS IoT."
    },
    {
        "id": "scene2_opencv_spatial",
        "text": "AuraVision calculates dense optical flow vector fields at sixty frames per second directly on the edge. By projecting three-dimensional bounding frustums and kinematic velocity vectors, AuraVision continuously monitors the operational safety envelope in real time."
    },
    {
        "id": "scene3_ttc_interception",
        "text": "Here, when a worker enters the path of an automated guided vehicle, AuraVision computes the exact Time-To-Collision. As the trajectory crosses the lateral safety corridor with a sub-one-point-two second threshold, AuraVision instantly triggers an emergency braking interception."
    },
    {
        "id": "scene4_aws_greengrass",
        "text": "Simultaneously, AuraVision synchronizes high-priority hazard events to AWS IoT Greengrass with guaranteed Quality of Service over lightweight MQTT topics, ensuring full cloud observability without incurring high-latency round-trip bottlenecks."
    },
    {
        "id": "scene5_cli_closing",
        "text": "With full multi-entity swarm tracking and a deterministic terminal CLI, AuraVision delivers sub-four-millisecond spatial intelligence. Open source, robust, and engineered for next-generation physical AI safety."
    }
]

async def generate_scene_audio():
    output_dir = os.path.dirname(__file__)
    for idx, scene in enumerate(SCENES):
        mp3_path = os.path.join(output_dir, f"{scene['id']}.mp3")
        print(f"Generating audio for Scene {idx+1}: {scene['id']}...")
        communicate = edge_tts.Communicate(scene['text'], VOICE, rate=RATE, pitch=PITCH)
        await communicate.save(mp3_path)
        print(f"Saved: {mp3_path}")

if __name__ == "__main__":
    asyncio.run(generate_scene_audio())
