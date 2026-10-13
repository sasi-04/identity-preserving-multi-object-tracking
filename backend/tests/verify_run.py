import urllib.request
import json

def main():
    req = urllib.request.Request(
        "http://127.0.0.1:8080/api/tracking-sessions",
        data=json.dumps({"source_type": "sample", "sample_name": "transit_gate_demo.mp4", "enable_oie": True}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    res = json.loads(urllib.request.urlopen(req).read())
    sid = res["session_id"]
    print("Session created:", sid)

    for i in range(50):
        step_req = urllib.request.Request(
            f"http://127.0.0.1:8080/api/tracking-sessions/{sid}/step?draw_bboxes=true&draw_ids=true&draw_trails=true",
            data=b"",
            headers={"Content-Type": "application/json"}
        )
        s_data = json.loads(urllib.request.urlopen(step_req).read())

    print("Successfully processed 50 frames without error!")
    print("Current frame index:", s_data["frame_idx"])
    print("Visible tracks count:", len(s_data["telemetry"]["tracks"]))
    print("All tracks count:", s_data["telemetry"]["all_tracks_count"])
    print("Confirmed tracks:", s_data["telemetry"]["confirmed_count"])
    print("Occluded tracks:", s_data["telemetry"]["occluded_count"])
    print("Recoveries count:", s_data["telemetry"]["recovered_count"])
    cpi = s_data["telemetry"]["crowd_pressure"]
    print("Crowd Pressure Index (CPI):", cpi["crowd_pressure_index"] if cpi else 0.0)
    print("FPS:", s_data["telemetry"]["fps"])
    print("Latency (ms):", s_data["telemetry"]["latency_ms"])

if __name__ == "__main__":
    main()
