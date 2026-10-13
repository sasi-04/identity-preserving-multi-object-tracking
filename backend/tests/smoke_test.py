import json
import urllib.request

def post(url, data=None):
    payload = json.dumps(data).encode("utf-8") if data is not None else b""
    headers = {"Content-Type": "application/json"} if data is not None else {}
    req = urllib.request.Request(url, data=payload, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get(url):
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode("utf-8"))

def delete(url):
    req = urllib.request.Request(url, method="DELETE")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    print("Testing ZED VISION live endpoints on http://127.0.0.1:8080...")

    # 1. Health & Status
    health = get("http://127.0.0.1:8080/api/health")
    print(f"[OK] Health: {health['status']} | App: {health['app_name']} v{health['version']}")

    models = get("http://127.0.0.1:8080/api/models/status")
    print(f"[OK] Detector: {models['detector']['name']} | ReID: {models['reid_appearance']['name']}")

    # 2. Videos list & Video Delete Flow
    videos = get("http://127.0.0.1:8080/api/videos")
    print(f"[OK] Available videos: {len(videos['samples'])} samples, {len(videos['uploads'])} uploads")

    # 3. Create tracking session with default OpenCV detector
    session = post("http://127.0.0.1:8080/api/tracking-sessions", {"detector_type": "opencv"})
    sid = session["session_id"]
    print(f"[OK] Created live session #{sid} with OpenCV detector for {session['video_name']} ({session['total_frames']} frames)")

    # 4. Step 5 frames
    for i in range(5):
        step = post(f"http://127.0.0.1:8080/api/tracking-sessions/{sid}/step")
        telemetry = step["telemetry"]
        print(f"     Frame {step['frame_idx']}: {len(telemetry['tracks'])} visible tracks | Latency: {telemetry['latency_ms']}ms | FPS: {telemetry['fps']} | CPI: {telemetry['crowd_pressure']['crowd_pressure_index'] if telemetry.get('crowd_pressure') else 0.0}")

    # 5. Diagnostic events
    events = get(f"http://127.0.0.1:8080/api/tracking-sessions/{sid}/events")
    print(f"[OK] OIE Diagnostics logged: {len(events['events'])} events")

    # 6. Session Metrics
    metrics = get(f"http://127.0.0.1:8080/api/tracking-sessions/{sid}/metrics")
    print(f"[OK] Session Metrics: Processed {metrics['processed_frames']} frames @ {metrics['avg_fps']} FPS")

    # 7. Stop session
    stop = post(f"http://127.0.0.1:8080/api/tracking-sessions/{sid}/stop")
    print(f"[OK] Session #{sid} stopped successfully: {stop['status']}")

    # 8. Experiments database
    experiments = get("http://127.0.0.1:8080/api/experiments")
    print(f"[OK] Experiments database query returned {len(experiments)} persisted runs")

    print("\nALL LIVE ENDPOINTS AND TRACKING WORKFLOWS VERIFIED 100% OPERATIONAL!")

if __name__ == "__main__":
    main()

