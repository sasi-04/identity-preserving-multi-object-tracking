import { useEffect, useRef, useState, type FC, type ChangeEvent } from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  StepForward,
  Upload,
  Layers,
  Trash2,
  Star,
  Check
} from 'lucide-react';
import {
  createTrackingSession,
  fetchVideos,
  pauseSession,
  resetSession,
  resumeSession,
  stepSession,
  uploadVideo,
  deleteVideo,
  stopSession
} from '../services/api';
import type { FrameTelemetry, TrackData, TrackerSettings } from '../types/tracking';

interface LiveTrackingStudioProps {
  activeSessionId: string | null;
  setActiveSessionId: (id: string | null) => void;
  onTelemetryUpdate: (telemetry: FrameTelemetry) => void;
  settings?: TrackerSettings;
}

export const LiveTrackingStudio: FC<LiveTrackingStudioProps> = ({
  activeSessionId,
  setActiveSessionId,
  onTelemetryUpdate,
  settings
}) => {
  const [videoList, setVideoList] = useState<{ samples: any[]; uploads: any[] }>({ samples: [], uploads: [] });
  const [selectedVideo, setSelectedVideo] = useState<string>('');
  const [detectorType, setDetectorType] = useState<string>('opencv');
  const [defaultVideo, setDefaultVideo] = useState<string>(() => localStorage.getItem('zed_default_video') || '');
  const [feedbackMsg, setFeedbackMsg] = useState<string>('');

  // Player state
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [currentFrame, setCurrentFrame] = useState<number>(0);
  const [totalFrames, setTotalFrames] = useState<number>(150);
  const [frameImage, setFrameImage] = useState<string>('');
  const [telemetry, setTelemetry] = useState<FrameTelemetry | null>(null);

  // Overlays
  const [showBboxes, setShowBboxes] = useState<boolean>(true);
  const [showIds, setShowIds] = useState<boolean>(true);
  const [showTrails, setShowTrails] = useState<boolean>(true);

  const [loading, setLoading] = useState<boolean>(false);

  // Synchronization refs to eliminate race conditions and stale closures
  const isPlayingRef = useRef<boolean>(false);
  const playbackTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const sessionGenRef = useRef<number>(0);
  const activeSessionIdRef = useRef<string | null>(null);
  activeSessionIdRef.current = activeSessionId;

  const showBboxesRef = useRef<boolean>(showBboxes);
  showBboxesRef.current = showBboxes;
  const showIdsRef = useRef<boolean>(showIds);
  showIdsRef.current = showIds;
  const showTrailsRef = useRef<boolean>(showTrails);
  showTrailsRef.current = showTrails;

  // Imperative playback control
  const stopPlayback = () => {
    setIsPlaying(false);
    isPlayingRef.current = false;
    if (playbackTimerRef.current) {
      clearTimeout(playbackTimerRef.current);
      playbackTimerRef.current = null;
    }
  };

  const startPlayback = (targetSessionId: string, generation: number) => {
    if (playbackTimerRef.current) {
      clearTimeout(playbackTimerRef.current);
      playbackTimerRef.current = null;
    }

    setIsPlaying(true);
    isPlayingRef.current = true;

    const loop = async () => {
      if (!isPlayingRef.current || sessionGenRef.current !== generation) {
        return;
      }

      try {
        let res = await stepSession(
          targetSessionId,
          showBboxesRef.current,
          showIdsRef.current,
          showTrailsRef.current
        );

        if (!isPlayingRef.current || sessionGenRef.current !== generation) {
          return;
        }

        if (res) {
          // If video reached the end, automatically loop from frame 0
          if (res.is_finished) {
            await resetSession(targetSessionId);
            if (!isPlayingRef.current || sessionGenRef.current !== generation) return;
            res = await stepSession(
              targetSessionId,
              showBboxesRef.current,
              showIdsRef.current,
              showTrailsRef.current
            );
            if (!isPlayingRef.current || sessionGenRef.current !== generation) return;
          }

          if (res && res.image) {
            setFrameImage(res.image);
            setCurrentFrame(res.frame_idx);
            setTelemetry(res.telemetry);
            onTelemetryUpdate(res.telemetry);
          }

          // Schedule next frame (~30 FPS playback)
          if (isPlayingRef.current && sessionGenRef.current === generation) {
            playbackTimerRef.current = setTimeout(loop, 33);
          }
        } else {
          stopPlayback();
        }
      } catch (err) {
        console.error('Playback step error:', err);
        if (sessionGenRef.current === generation) {
          stopPlayback();
        }
      }
    };

    playbackTimerRef.current = setTimeout(loop, 33);
  };

  // Single source of truth for switching videos or detectors cleanly
  const switchVideoOrDetector = async (newVid: string, newDet: string = detectorType) => {
    if (!newVid) return;

    // 1. Immediately invalidate any running loop & cancel timer
    sessionGenRef.current += 1;
    const currentGen = sessionGenRef.current;
    stopPlayback();
    setLoading(true);

    // 2. Stop old session on backend
    const oldId = activeSessionIdRef.current;
    if (oldId) {
      try {
        await stopSession(oldId);
      } catch (err) {
        // Ignore stop error if already stopped
      }
    }
    if (sessionGenRef.current !== currentGen) return;

    // 3. Reset UI state cleanly for the new video
    setCurrentFrame(0);
    setFrameImage('');
    setTelemetry(null);
    onTelemetryUpdate({
      frame_idx: 0,
      tracks: [],
      active_tracks_count: 0,
      occluded_tracks_count: 0,
      confirmed_tracks_count: 0,
      all_tracks_count: 0,
      total_id_switches: 0,
      total_recoveries: 0,
      causal_latency_ms: 0,
      fps: 0,
      crowd_density: 0,
      crowd_pressure: 0,
      current_occlusions: 0,
    } as any);

    try {
      // 4. Create new tracking session
      const res = await createTrackingSession(newVid, settings, newDet);
      if (sessionGenRef.current !== currentGen) {
        stopSession(res.session_id).catch(() => {});
        return;
      }

      setActiveSessionId(res.session_id);
      activeSessionIdRef.current = res.session_id;
      setTotalFrames(res.total_frames);
      setCurrentFrame(0);

      // 5. Causally step initial frame 0
      const firstStep = await stepSession(
        res.session_id,
        showBboxesRef.current,
        showIdsRef.current,
        showTrailsRef.current
      );
      if (sessionGenRef.current !== currentGen) {
        stopSession(res.session_id).catch(() => {});
        return;
      }

      if (firstStep && firstStep.image) {
        setFrameImage(firstStep.image);
        setCurrentFrame(firstStep.frame_idx);
        setTelemetry(firstStep.telemetry);
        onTelemetryUpdate(firstStep.telemetry);
      }

      // 6. Automatically start playing the new video immediately!
      startPlayback(res.session_id, currentGen);
    } catch (e) {
      console.error('Failed to switch video/session:', e);
      if (sessionGenRef.current === currentGen) {
        stopPlayback();
      }
    } finally {
      if (sessionGenRef.current === currentGen) {
        setLoading(false);
      }
    }
  };

  // Load available videos on mount and automatically run default video
  useEffect(() => {
    fetchVideos().then((data) => {
      setVideoList(data);
      const savedDefault = localStorage.getItem('zed_default_video');
      let targetVid = '';

      const allVids = [...data.uploads, ...data.samples];
      const match = allVids.find(v => v.path === savedDefault || v.name === savedDefault);
      if (match) {
        targetVid = match.path;
      } else if (data.uploads.length > 0) {
        targetVid = data.uploads[0].path;
      } else if (data.samples.length > 0) {
        targetVid = data.samples[0].path;
      }

      if (targetVid) {
        setSelectedVideo(targetVid);
        // Automatically start live tracking and play on open!
        switchVideoOrDetector(targetVid, 'opencv');
      }
    });

    return () => {
      // Cleanup on unmount: invalidate loop and stop active session
      sessionGenRef.current += 1;
      stopPlayback();
      const sid = activeSessionIdRef.current;
      if (sid) {
        stopSession(sid).catch(() => {});
      }
    };
  }, []);

  // Set default video handler
  const handleSetDefaultVideo = () => {
    if (!selectedVideo) return;
    localStorage.setItem('zed_default_video', selectedVideo);
    setDefaultVideo(selectedVideo);
    const name = selectedVideo.split(/[/\\]/).pop();
    setFeedbackMsg(`Default video set: ${name}`);
    setTimeout(() => setFeedbackMsg(''), 3000);
  };

  // Delete video handler
  const handleDeleteVideo = async () => {
    if (!selectedVideo) return;
    const filename = selectedVideo.split(/[/\\]/).pop() || '';
    if (!window.confirm(`Are you sure you want to delete ${filename}?`)) return;

    try {
      setLoading(true);
      stopPlayback();
      await deleteVideo(selectedVideo);
      if (localStorage.getItem('zed_default_video') === selectedVideo) {
        localStorage.removeItem('zed_default_video');
        setDefaultVideo('');
      }
      const data = await fetchVideos();
      setVideoList(data);
      const nextVid = data.uploads.length > 0 ? data.uploads[0].path : (data.samples.length > 0 ? data.samples[0].path : '');
      setSelectedVideo(nextVid);
      if (nextVid) {
        await switchVideoOrDetector(nextVid, detectorType);
      } else {
        setActiveSessionId(null);
        activeSessionIdRef.current = null;
        setFrameImage('');
        setCurrentFrame(0);
        setTelemetry(null);
      }
      setFeedbackMsg(`Deleted ${filename}`);
      setTimeout(() => setFeedbackMsg(''), 3000);
    } catch (err: any) {
      alert(`Failed to delete video: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Step single frame causally
  const handleStep = async () => {
    const sid = activeSessionIdRef.current;
    if (!sid) {
      await switchVideoOrDetector(selectedVideo, detectorType);
      return;
    }
    stopPlayback();
    try {
      const res = await stepSession(
        sid,
        showBboxesRef.current,
        showIdsRef.current,
        showTrailsRef.current
      );
      if (res && res.image) {
        setFrameImage(res.image);
        setCurrentFrame(res.frame_idx);
        setTelemetry(res.telemetry);
        onTelemetryUpdate(res.telemetry);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Play / pause toggle
  const handleTogglePlay = async () => {
    const sid = activeSessionIdRef.current;
    if (!sid) {
      await switchVideoOrDetector(selectedVideo, detectorType);
      return;
    }

    if (isPlayingRef.current) {
      stopPlayback();
      await pauseSession(sid).catch(() => {});
    } else {
      await resumeSession(sid).catch(() => {});
      startPlayback(sid, sessionGenRef.current);
    }
  };

  // Reset handler: resets session to frame 0 and auto-plays
  const handleReset = async () => {
    const sid = activeSessionIdRef.current;
    if (!sid) return;
    stopPlayback();
    try {
      await resetSession(sid);
      setCurrentFrame(0);
      const res = await stepSession(
        sid,
        showBboxesRef.current,
        showIdsRef.current,
        showTrailsRef.current
      );
      if (res && res.image) {
        setFrameImage(res.image);
        setCurrentFrame(res.frame_idx);
        setTelemetry(res.telemetry);
        onTelemetryUpdate(res.telemetry);
      }
      startPlayback(sid, sessionGenRef.current);
    } catch (e) {
      console.error(e);
    }
  };

  const handleFileUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    try {
      setLoading(true);
      const res = await uploadVideo(file);
      const updated = await fetchVideos();
      setVideoList(updated);
      setSelectedVideo(res.path);
      setDetectorType('opencv');
      // Auto-start live inference immediately on uploaded video!
      await switchVideoOrDetector(res.path, 'opencv');
      setFeedbackMsg(`Uploaded & streaming: ${res.filename}`);
      setTimeout(() => setFeedbackMsg(''), 3000);
    } catch (err) {
      console.error(err);
      alert('Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const isUploadedVideo = videoList.uploads.some((v) => v.path === selectedVideo);
  const isCurrentDefault = defaultVideo === selectedVideo;

  return (
    <div>
      {/* Studio Control Toolbar */}
      <div
        className="zed-card"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          marginBottom: '1rem',
          padding: '0.85rem 1.25rem',
        }}
      >
        {/* Source video selection and action controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
          <label style={{ fontSize: '12.5px', color: 'var(--text-secondary)', fontWeight: 500 }}>
            Input Stream:
          </label>
          <select
            value={selectedVideo}
            onChange={(e) => {
              const newVid = e.target.value;
              setSelectedVideo(newVid);
              switchVideoOrDetector(newVid, detectorType);
            }}
            style={{
              background: 'var(--bg-tertiary)',
              color: '#fff',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              padding: '0.45rem 0.75rem',
              fontSize: '13px',
              cursor: 'pointer',
              minWidth: '220px',
            }}
          >
            {videoList.uploads.length > 0 && (
              <optgroup label="Uploaded Videos (Custom)">
                {videoList.uploads.map((v) => (
                  <option key={v.path} value={v.path}>
                    {v.name} ({v.size_mb} MB) {defaultVideo === v.path ? ' ★ [Default]' : ''}
                  </option>
                ))}
              </optgroup>
            )}
            <optgroup label="Sample Benchmarks">
              {videoList.samples.map((v) => (
                <option key={v.path} value={v.path}>
                  {v.name} ({v.size_mb} MB) {defaultVideo === v.path ? ' ★ [Default]' : ''}
                </option>
              ))}
            </optgroup>
          </select>

          {/* Set as Default Video Button */}
          <button
            onClick={handleSetDefaultVideo}
            className="zed-btn zed-btn-secondary"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              fontSize: '12.5px',
              padding: '0.45rem 0.7rem',
              borderColor: isCurrentDefault ? '#f59e0b' : 'var(--border-subtle)',
              color: isCurrentDefault ? '#f59e0b' : 'var(--text-secondary)',
              cursor: 'pointer'
            }}
            title="Set this video as default to automatically run when opening Live Tracking Studio"
          >
            <Star size={13} fill={isCurrentDefault ? '#f59e0b' : 'none'} color={isCurrentDefault ? '#f59e0b' : '#aaa'} />
            <span>{isCurrentDefault ? 'Default Video' : 'Set Default'}</span>
          </button>

          {/* Delete Video Button (Active for Uploaded Videos) */}
          {isUploadedVideo && (
            <button
              onClick={handleDeleteVideo}
              className="zed-btn zed-btn-secondary"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
                fontSize: '12.5px',
                padding: '0.45rem 0.7rem',
                borderColor: 'rgba(229, 9, 20, 0.5)',
                color: 'var(--zed-red)',
                cursor: 'pointer'
              }}
              title="Delete this uploaded video file"
            >
              <Trash2 size={13} />
              <span>Delete</span>
            </button>
          )}

          {/* Detector Selector - OpenCV Default */}
          <select
            value={detectorType}
            onChange={(e) => {
              const newDet = e.target.value;
              setDetectorType(newDet);
              switchVideoOrDetector(selectedVideo, newDet);
            }}
            style={{
              background: 'var(--bg-tertiary)',
              color: '#fff',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              padding: '0.45rem 0.75rem',
              fontSize: '13px',
              cursor: 'pointer',
            }}
          >
            <option value="opencv">OpenCV DNN & Multi-Scale Person (Default)</option>
            <option value="synthetic">Synthetic Flow Detector (Offline)</option>
          </select>

          <label className="btn-secondary" style={{ cursor: 'pointer', margin: 0, display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '12.5px', padding: '0.45rem 0.75rem' }}>
            <Upload size={14} />
            <span>Upload Video</span>
            <input
              type="file"
              accept="video/mp4,video/avi,video/mov"
              style={{ display: 'none' }}
              onChange={handleFileUpload}
            />
          </label>

          <button className="btn-secondary" onClick={() => switchVideoOrDetector(selectedVideo, detectorType)} disabled={loading} style={{ fontSize: '12.5px', padding: '0.45rem 0.75rem' }}>
            {loading ? 'Initializing...' : 'Reset'}
          </button>

          {feedbackMsg && (
            <span style={{ fontSize: '12px', color: '#10b981', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <Check size={13} /> {feedbackMsg}
            </span>
          )}
        </div>

        {/* Video Overlay Toggles */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '12.5px' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={showBboxes}
              onChange={(e) => setShowBboxes(e.target.checked)}
              style={{ accentColor: 'var(--zed-red)' }}
            />
            <span>Bounding Boxes</span>
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={showIds}
              onChange={(e) => setShowIds(e.target.checked)}
              style={{ accentColor: 'var(--zed-red)' }}
            />
            <span>Track IDs</span>
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={showTrails}
              onChange={(e) => setShowTrails(e.target.checked)}
              style={{ accentColor: 'var(--zed-red)' }}
            />
            <span>Motion Trails</span>
          </label>
        </div>
      </div>

      {/* Main Studio Viewport & Active Tracks Split */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '1.25rem' }}>
        {/* Left Viewport & Player Controls */}
        <div>
          <div
            className="zed-card"
            style={{
              padding: 0,
              overflow: 'hidden',
              background: '#040406',
              display: 'flex',
              flexDirection: 'column',
              aspectRatio: '16 / 9',
              position: 'relative',
              justifyContent: 'center',
              alignItems: 'center',
            }}
          >
            {frameImage ? (
              <img
                src={frameImage}
                alt="Tracking Output"
                style={{ width: '100%', height: '100%', objectFit: 'contain' }}
              />
            ) : loading ? (
              <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                <div style={{ margin: '0 auto 0.75rem', width: '32px', height: '32px', border: '3px solid rgba(255,255,255,0.2)', borderTopColor: 'var(--zed-red)', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
                <div style={{ fontSize: '14px', fontWeight: 600, color: '#fff' }}>Initializing & Loading Video...</div>
                <div style={{ fontSize: '12px', marginTop: '0.25rem', color: 'var(--text-secondary)' }}>Preparing causal tracker and auto-playing</div>
              </div>
            ) : (
              <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                <Layers size={40} style={{ margin: '0 auto 0.5rem', opacity: 0.4 }} />
                <div style={{ fontSize: '14px', fontWeight: 600 }}>Causal Tracking Viewport Ready</div>
                <div style={{ fontSize: '12px', marginTop: '0.25rem' }}>Select an input stream or click Play to begin</div>
              </div>
            )}
          </div>

          {/* Player Controls Bar */}
          <div
            className="zed-card"
            style={{
              marginTop: '0.75rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0.65rem 1rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <button
                className={isPlaying ? 'btn-secondary' : 'btn-primary'}
                onClick={handleTogglePlay}
                style={{ minWidth: '95px', justifyContent: 'center' }}
              >
                {isPlaying ? <Pause size={15} /> : <Play size={15} fill="currentColor" />}
                <span>{isPlaying ? 'Pause' : 'Play'}</span>
              </button>

              <button className="btn-secondary" onClick={handleStep} title="Single-frame causal step">
                <StepForward size={15} />
                <span>Step</span>
              </button>

              <button className="btn-secondary" onClick={handleReset} title="Reset to frame 0">
                <RotateCcw size={15} />
              </button>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', fontSize: '12.5px', fontFamily: 'JetBrains Mono' }}>
              <div>
                Frame: <strong style={{ color: '#fff' }}>{currentFrame}</strong> / {totalFrames}
              </div>
              <div>
                Latency: <strong style={{ color: 'var(--color-confirmed)' }}>{telemetry?.latency_ms ?? 0}ms</strong>
              </div>
              <div>
                FPS: <strong style={{ color: '#fff' }}>{telemetry?.fps ?? 0}</strong>
              </div>
            </div>
          </div>
        </div>

        {/* Right Active Tracks Table */}
        <div className="zed-card" style={{ display: 'flex', flexDirection: 'column', maxHeight: '620px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>
              Active Tracks ({telemetry?.tracks?.length ?? 0})
            </h3>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Causal Memory</span>
          </div>

          <div style={{ flex: 1, overflowY: 'auto' }}>
            <table className="zed-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>State</th>
                  <th>Conf</th>
                  <th>Quality</th>
                </tr>
              </thead>
              <tbody>
                {telemetry?.tracks && telemetry.tracks.length > 0 ? (
                  telemetry.tracks.map((t: TrackData) => {
                    let badgeClass = 'badge-tentative';
                    if (t.state === 'CONFIRMED') badgeClass = 'badge-confirmed';
                    else if (t.state === 'OCCLUDED' || t.state === 'LOST') badgeClass = 'badge-occluded';
                    else if (t.state === 'RECOVERED') badgeClass = 'badge-recovered';

                    return (
                      <tr key={t.track_id}>
                        <td style={{ fontWeight: 700, fontFamily: 'JetBrains Mono' }}>#{t.track_id}</td>
                        <td>
                          <span className={`badge ${badgeClass}`}>{t.state.slice(0, 4)}</span>
                        </td>
                        <td style={{ fontFamily: 'JetBrains Mono' }}>{(t.confidence * 100).toFixed(0)}%</td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                            <div
                              style={{
                                width: '40px',
                                height: '5px',
                                background: 'var(--border-subtle)',
                                borderRadius: '3px',
                                overflow: 'hidden',
                              }}
                            >
                              <div
                                style={{
                                  width: `${Math.round(t.crop_quality * 100)}%`,
                                  height: '100%',
                                  background: t.crop_quality > 0.5 ? 'var(--color-confirmed)' : 'var(--color-occluded)',
                                }}
                              />
                            </div>
                            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                              {(t.crop_quality * 100).toFixed(0)}%
                            </span>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={4} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem 1rem' }}>
                      No active tracks in viewport
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
