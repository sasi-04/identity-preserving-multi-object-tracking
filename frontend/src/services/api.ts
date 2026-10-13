import type {
  ExperimentRun,
  FrameTelemetry,
  MOTMetrics,
  TrackingSessionInfo,
  TrackerSettings
} from '../types/tracking';

const BASE_URL = '/api';

export async function fetchHealth(): Promise<{ status: string; app_name: string; version: string }> {
  const res = await fetch(`${BASE_URL}/health`);
  if (!res.ok) throw new Error('Failed to fetch health');
  return res.json();
}

export async function fetchModelStatus(): Promise<any> {
  const res = await fetch(`${BASE_URL}/models/status`);
  if (!res.ok) throw new Error('Failed to fetch model status');
  return res.json();
}

export async function fetchSystemStatus(): Promise<any> {
  const res = await fetch(`${BASE_URL}/system/status`);
  if (!res.ok) throw new Error('Failed to fetch system status');
  return res.json();
}

export async function fetchVideos(): Promise<{ samples: any[]; uploads: any[] }> {
  const res = await fetch(`${BASE_URL}/videos`);
  if (!res.ok) throw new Error('Failed to list videos');
  return res.json();
}

export async function uploadVideo(file: File): Promise<any> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${BASE_URL}/videos/upload`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) throw new Error('Upload failed');
  return res.json();
}

export async function deleteVideo(videoPath: string): Promise<any> {
  const filename = videoPath.split(/[/\\]/).pop();
  const res = await fetch(`${BASE_URL}/videos/${encodeURIComponent(filename || '')}`, {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error('Delete failed');
  return res.json();
}


export async function createTrackingSession(
  videoPath?: string,
  config?: Partial<TrackerSettings>,
  detectorType: string = 'opencv'
): Promise<TrackingSessionInfo> {
  const res = await fetch(`${BASE_URL}/tracking-sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      video_path: videoPath,
      detector_type: detectorType,
      config: config
    })
  });
  if (!res.ok) throw new Error('Failed to create tracking session');
  return res.json();
}

export async function stepSession(
  sessionId: string,
  drawBboxes: boolean = true,
  drawIds: boolean = true,
  drawTrails: boolean = true
): Promise<{
  session_id: string;
  frame_idx: number;
  total_frames: number;
  image: string;
  telemetry: FrameTelemetry;
  is_finished: boolean;
}> {
  const url = `${BASE_URL}/tracking-sessions/${sessionId}/step?draw_bboxes=${drawBboxes}&draw_ids=${drawIds}&draw_trails=${drawTrails}`;
  const res = await fetch(url, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to step frame');
  return res.json();
}

export async function startSession(sessionId: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/tracking-sessions/${sessionId}/start`, { method: 'POST' });
  return res.json();
}

export async function pauseSession(sessionId: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/tracking-sessions/${sessionId}/pause`, { method: 'POST' });
  return res.json();
}

export async function resumeSession(sessionId: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/tracking-sessions/${sessionId}/resume`, { method: 'POST' });
  return res.json();
}

export async function resetSession(sessionId: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/tracking-sessions/${sessionId}/reset`, { method: 'POST' });
  return res.json();
}

export async function stopSession(sessionId: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/tracking-sessions/${sessionId}/stop`, { method: 'POST' });
  return res.json();
}

export async function fetchSessionEvents(sessionId: string): Promise<{ session_id: string; events: any[] }> {
  const res = await fetch(`${BASE_URL}/tracking-sessions/${sessionId}/events`);
  if (!res.ok) throw new Error('Failed to fetch events');
  return res.json();
}

export async function fetchSessionMetrics(sessionId: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/tracking-sessions/${sessionId}/metrics`);
  if (!res.ok) throw new Error('Failed to fetch metrics');
  return res.json();
}

export async function fetchExperiments(): Promise<ExperimentRun[]> {
  const res = await fetch(`${BASE_URL}/experiments`);
  if (!res.ok) throw new Error('Failed to fetch experiments');
  return res.json();
}

export async function runExperiment(
  name: string,
  config?: Partial<TrackerSettings>
): Promise<ExperimentRun> {
  const res = await fetch(`${BASE_URL}/experiments/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, config })
  });
  if (!res.ok) throw new Error('Failed to run experiment');
  return res.json();
}

export async function runAblationStudy(): Promise<{ status: string; results: Record<string, MOTMetrics> }> {
  const res = await fetch(`${BASE_URL}/evaluations/run-ablation`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to run ablation study');
  return res.json();
}

export async function fetchDatasetInfo(): Promise<any> {
  const res = await fetch(`${BASE_URL}/evaluations/dataset-info`);
  if (!res.ok) throw new Error('Failed to fetch dataset info');
  return res.json();
}
