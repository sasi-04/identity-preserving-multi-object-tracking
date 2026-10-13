export type TrackState = "TENTATIVE" | "CONFIRMED" | "OCCLUDED" | "LOST" | "RECOVERED" | "EXPIRED";

export interface TrackData {
  track_id: number;
  state: TrackState;
  bbox: [number, number, number, number];
  confidence: number;
  hits: number;
  age: number;
  time_since_update: number;
  trajectory: [number, number][];
  crop_quality: number;
  occlusion_overlap: number;
  uncertainty_radius: number;
  recovery_count: number;
}

export interface CrowdPressure {
  frame_idx: number;
  active_pedestrian_count: number;
  mean_overlap_iou: number;
  max_overlap_iou: number;
  crowd_pressure_index: number;
  ambiguity_rate: number;
  occluded_tracks_count: number;
}

export interface DiagnosticRecord {
  event_type: "RECOVERY_CONFIRMED" | "AMBIGUOUS_REJECTED" | "OCCLUSION_ENTER" | "LOST_ENTER" | "GATING_REJECTED";
  track_id: number;
  frame_idx: number;
  timestamp: number;
  previous_bbox: [number, number, number, number];
  predicted_bbox: [number, number, number, number];
  candidate_bbox?: [number, number, number, number];
  motion_cost: number;
  appearance_cost: number;
  geometry_cost: number;
  final_cost: number;
  decision_reason: string;
  is_confirmed: boolean;
  ambiguity_margin?: number;
  spatial_uncertainty_px: number;
}

export interface FrameTelemetry {
  frame_idx: number;
  tracks: TrackData[];
  all_tracks_count: number;
  confirmed_count: number;
  occluded_count: number;
  recovered_count: number;
  total_detections: number;
  crowd_pressure?: CrowdPressure;
  diagnostics: DiagnosticRecord[];
  latency_ms: number;
  fps: number;
}

export interface TrackingSessionInfo {
  session_id: string;
  video_name: string;
  total_frames: number;
  fps: number;
  is_oie: boolean;
}

export interface MOTMetrics {
  idf1: number;
  idp: number;
  idr: number;
  idsw: number;
  mota: number;
  hota: number;
  deta: number;
  assa: number;
  mostly_tracked: number;
  mostly_lost: number;
  total_gt_ids: number;
  total_pred_ids: number;
  fps: number;
  latency_ms: number;
}

export interface ExperimentRun {
  id: string;
  name: string;
  created_at: string;
  video_name: string;
  is_oie: boolean;
  config: Record<string, any>;
  metrics: MOTMetrics;
  status: string;
}

export interface TrackerSettings {
  min_hits_to_confirm: number;
  lost_timeout_frames: number;
  max_lost_frames: number;
  high_det_thresh: number;
  low_det_thresh: number;
  match_iou_thresh_stage1: number;
  match_iou_thresh_stage2: number;
  weight_motion: number;
  weight_appearance: number;
  weight_geometry: number;
  enable_oie: boolean;
  enable_uncertainty_recovery: boolean;
  enable_adaptive_weights: boolean;
  enable_temporal_memory: boolean;
  enable_ambiguity_rejection: boolean;
  ambiguity_margin_threshold: number;
  appearance_memory_size: number;
  gap_penalty_factor: number;
}
