import React, { useEffect, useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiRequest } from '../api/client';
import { 
  Clock, ShieldCheck, CheckCircle2, AlertTriangle, 
  ChevronLeft, ChevronRight, Bookmark, Send, Award, Play,
  Camera, Mic, Eye, ShieldAlert, UserCheck, Layers, Lock,
  Building2, Sparkles, AlertCircle, FileCode, CheckCircle
} from 'lucide-react';

// ── Company-Specific Pattern Configurations ─────────────────────────────────
const COMPANY_THEME: Record<string, {
  name: string;
  badge: string;
  color: string;
  bg: string;
  border: string;
  emoji: string;
  guidance: string[];
}> = {
  TCS_ION: {
    name: 'TCS iON Examination Environment',
    badge: 'TCS iON NQT Pattern',
    color: '#60A5FA',
    bg: 'rgba(59, 130, 246, 0.14)',
    border: 'rgba(59, 130, 246, 0.35)',
    emoji: '🔵',
    guidance: [
      'Sectional Sequence: Part A Foundation (Numerical, Verbal, Reasoning) followed by Part B Advanced Hands-On Coding.',
      'Negative marking (-0.25) applies to selective multiple-choice sections.',
      'AI biometric presence, tab departures, and full-screen telemetry continuously monitored.',
    ]
  },
  INFOSYS_INFYTQ: {
    name: 'Infosys InfyTQ / Springboard Assessment',
    badge: 'Infosys SP / DSE Pattern',
    color: '#A78BFA',
    bg: 'rgba(167, 139, 250, 0.14)',
    border: 'rgba(167, 139, 250, 0.35)',
    emoji: '🟣',
    guidance: [
      'Focus areas: Algorithm Design, Python/Java Problem Solving, and Analytical Aptitude.',
      'Sectional cut-offs apply to qualify for Specialist Programmer (SP) and Digital Specialist (DSE) interviews.',
      'Strict test isolation: Window blurs and clipboard paste events deduct from session integrity.',
    ]
  },
  WIPRO_AMCAT: {
    name: 'Wipro TalentNext / AMCAT Test Drive',
    badge: 'Wipro AMCAT Pattern',
    color: '#34D399',
    bg: 'rgba(52, 211, 153, 0.14)',
    border: 'rgba(52, 211, 153, 0.35)',
    emoji: '🟢',
    guidance: [
      'Domain assessment covering quantitative aptitude, programming logic, and code debugging.',
      'Sequential answering: Questions must be answered in structured order without premature skipping.',
      'Automated telemetry monitors audio levels and secondary screen devices.',
    ]
  },
  ACCENTURE_COGNITIVE: {
    name: 'Accenture Cognitive & Technical Assessment',
    badge: 'Accenture Pattern',
    color: '#FBBF24',
    bg: 'rgba(251, 191, 36, 0.14)',
    border: 'rgba(251, 191, 36, 0.35)',
    emoji: '🟠',
    guidance: [
      'Cognitive assessment & technical coding challenges with strict non-pausable countdown.',
      'Real-time automated saving after each option selection.',
      'Automated grading and candidate performance benchmarking upon final review submission.',
    ]
  },
  CUSTOM: {
    name: 'AssessIQ Verified Examination',
    badge: 'Standard Proctored Pattern',
    color: '#818CF8',
    bg: 'rgba(99, 102, 241, 0.14)',
    border: 'rgba(99, 102, 241, 0.35)',
    emoji: '🛡️',
    guidance: [
      'Verified technical assessment delivered on the AssessIQ Cloud Examination Platform.',
      'Non-pausable timer with auto-submit upon duration expiration.',
      'Continuous anti-cheat proctoring and real-time response telemetry active.',
    ]
  }
};

// ── Timezone-Safe Date Parser ────────────────────────────────────────────────
const parseUtcDate = (dateStr: string | null | undefined): number => {
  if (!dateStr) return Date.now();
  // Ensure string without timezone suffix is treated as UTC
  const hasTz = dateStr.endsWith('Z') || dateStr.includes('+') || (dateStr.length > 10 && dateStr.lastIndexOf('-') > 10);
  const normalized = hasTz ? dateStr : `${dateStr}Z`;
  const parsed = new Date(normalized).getTime();
  return isNaN(parsed) ? Date.now() : parsed;
};

export const ExamRunnerPage: React.FC = () => {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();

  // Screen modes: 'LOADING' | 'META' (start screen) | 'RUNNER' (active test) | 'COMPLETED' (results)
  const [mode, setMode] = useState<'LOADING' | 'META' | 'RUNNER' | 'COMPLETED'>('LOADING');
  const [meta, setMeta] = useState<any | null>(null);
  const [session, setSession] = useState<any | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string[]>>({});
  const [markedForReview, setMarkedForReview] = useState<Set<number>>(new Set());
  const [saveStatus, setSaveStatus] = useState<string>('All answers saved');
  const [secondsRemaining, setSecondsRemaining] = useState<number>(1800);
  const [showSubmitModal, setShowSubmitModal] = useState(false);
  const [submissionResult, setSubmissionResult] = useState<any | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Active section filter for Question Navigator
  const [selectedSectionFilter, setSelectedSectionFilter] = useState<string>('ALL');

  // Sensory & Consent States
  const [cameraConsent, setCameraConsent] = useState(true);
  const [audioConsent, setAudioConsent] = useState(true);
  const [monitoringConsent, setMonitoringConsent] = useState(true);
  const [cameraActive, setCameraActive] = useState(false);

  // Proctoring telemetry
  const [proctorWarning, setProctorWarning] = useState<string | null>(null);
  const [integrityScore, setIntegrityScore] = useState<number>(100.0);

  // 1. Load Meta on mount
  useEffect(() => {
    const loadMeta = async () => {
      try {
        const res = await apiRequest(`/exam/${token}/meta`);
        setMeta(res);
        if (res.is_completed) {
          const finalRes = await apiRequest(`/exam/${token}/submit`, { method: 'POST' });
          setSubmissionResult(finalRes);
          setMode('COMPLETED');
        } else if (res.already_started) {
          await handleStartExam();
        } else {
          setMode('META');
        }
      } catch (err: any) {
        setError(err.message || 'Invalid or expired exam token');
        setMode('META');
      }
    };
    loadMeta();
  }, [token]);

  // 2. Start Exam Handler
  const handleStartExam = async () => {
    if (meta?.proctoring_mode !== 'LOW_FRICTION') {
      if (!cameraConsent || !audioConsent || !monitoringConsent) {
        setError('You must accept all monitoring permissions and proctoring disclosures to begin.');
        return;
      }
    } else {
      if (!monitoringConsent) {
        setError('You must accept behavioral monitoring to begin.');
        return;
      }
    }

    try {
      setMode('LOADING');
      // Record explicit candidate consent
      await apiRequest(`/exam/${token}/consent`, {
        method: 'POST',
        body: JSON.stringify({
          camera_consent_granted: cameraConsent,
          audio_consent_granted: audioConsent,
          browser_monitoring_consent: monitoringConsent,
          device_specs_json: {
            userAgent: navigator.userAgent,
            screenWidth: window.screen.width,
            screenHeight: window.screen.height,
          },
        }),
      });

      const res = await apiRequest(`/exam/${token}/start`, { method: 'POST' });
      setSession(res);
      setAnswers(res.saved_answers || {});

      // Calculate time remaining using timezone-safe UTC parser
      const endsAtMs = parseUtcDate(res.ends_at);
      const nowMs = Date.now();
      let remainingSec = Math.floor((endsAtMs - nowMs) / 1000);
      if (remainingSec <= 0 && res.duration_minutes) {
        remainingSec = res.duration_minutes * 60;
      }
      setSecondsRemaining(Math.max(10, remainingSec));
      setCameraActive(true);
      setMode('RUNNER');
    } catch (err: any) {
      setError(err.message || 'Failed to start exam session');
      setMode('META');
    }
  };

  // 3. Countdown Timer Interval
  useEffect(() => {
    if (mode !== 'RUNNER' || secondsRemaining <= 0) return;

    const interval = setInterval(() => {
      setSecondsRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          handleSubmitExam();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [mode, secondsRemaining]);

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  // 4. Option Select Handler (with real-time auto-save)
  const handleSelectOption = async (qId: string, optionId: string) => {
    const newSelected = [optionId];
    setAnswers((prev) => ({ ...prev, [qId]: newSelected }));
    setSaveStatus('Saving answer...');

    try {
      await apiRequest(`/exam/${token}/save-answer`, {
        method: 'POST',
        body: JSON.stringify({
          question_id: qId,
          selected_option_ids: newSelected,
        }),
      });
      setSaveStatus('All answers saved');
    } catch (err) {
      setSaveStatus('Error saving');
    }
  };

  // 5. Final Submit Handler
  const handleSubmitExam = async () => {
    setIsSubmitting(true);
    try {
      const res = await apiRequest(`/exam/${token}/submit`, { method: 'POST' });
      setSubmissionResult(res);
      setShowSubmitModal(false);
      setMode('COMPLETED');
    } catch (err: any) {
      alert(err.message || 'Failed to submit exam');
    } finally {
      setIsSubmitting(false);
    }
  };

  // 6. Proctoring telemetry dispatcher
  const recordProctorEvent = async (eventType: string, metadata: any = {}) => {
    if (mode !== 'RUNNER' || !token) return;
    try {
      const res = await apiRequest(`/exam/${token}/proctor/event`, {
        method: 'POST',
        body: JSON.stringify({
          event_type: eventType,
          metadata_json: metadata,
        }),
      });
      if (res && typeof res.integrity_score === 'number') {
        setIntegrityScore(res.integrity_score);
      }
    } catch (err) {
      console.warn('Failed to record proctoring event:', err);
    }
  };

  // Proctoring listeners (Tab switch, blur, paste, fullscreen exit)
  useEffect(() => {
    if (mode !== 'RUNNER') return;

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        setProctorWarning('⚠️ Warning: Tab departure detected! Exam activity is monitored and logged.');
        recordProctorEvent('TAB_SWITCH', { action: 'visibility_hidden', timestamp: new Date().toISOString() });
      }
    };

    const handleWindowBlur = () => {
      setProctorWarning('⚠️ Warning: Exam window lost focus! Please stay focused on the assessment.');
      recordProctorEvent('WINDOW_BLUR', { timestamp: new Date().toISOString() });
    };

    const handlePaste = () => {
      setProctorWarning('⚠️ Warning: Clipboard paste detected! External code pasting is restricted.');
      recordProctorEvent('PASTE_DETECTED', { timestamp: new Date().toISOString() });
    };

    const handleFullscreenChange = () => {
      if (!document.fullscreenElement) {
        setProctorWarning('⚠️ Warning: Fullscreen mode exited! Please maintain fullscreen during exam.');
        recordProctorEvent('FULLSCREEN_EXIT', { timestamp: new Date().toISOString() });
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('blur', handleWindowBlur);
    window.addEventListener('paste', handlePaste);
    document.addEventListener('fullscreenchange', handleFullscreenChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('blur', handleWindowBlur);
      window.removeEventListener('paste', handlePaste);
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, [mode, token]);

  const toggleMarkForReview = (index: number) => {
    const updated = new Set(markedForReview);
    if (updated.has(index)) updated.delete(index);
    else updated.add(index);
    setMarkedForReview(updated);
  };

  // Extract company pattern theme
  const currentPattern = meta?.company_pattern || session?.company_pattern || 'CUSTOM';
  const theme = COMPANY_THEME[currentPattern] || COMPANY_THEME.CUSTOM;

  // Sections list for navigator
  const sectionsList = useMemo(() => {
    if (!session?.questions) return [];
    const secSet = new Set<string>();
    session.questions.forEach((q: any) => {
      secSet.add(q.section_name || 'General');
    });
    return Array.from(secSet);
  }, [session]);

  // Code & Markdown content formatter
  const renderQuestionContent = (content: string) => {
    if (!content) return null;
    if (content.includes('```')) {
      const parts = content.split(/(```[\s\S]*?```)/g);
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
          {parts.map((part, idx) => {
            if (part.startsWith('```') && part.endsWith('```')) {
              const lines = part.slice(3, -3).trim().split('\n');
              const firstLine = lines[0].trim();
              const hasLang = lines.length > 1 && !firstLine.includes(' ') && firstLine.length < 15;
              const lang = hasLang ? firstLine : 'code';
              const code = hasLang ? lines.slice(1).join('\n') : lines.join('\n');
              return (
                <div key={idx} style={{
                  borderRadius: '8px',
                  overflow: 'hidden',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  backgroundColor: '#0a0d14',
                }}>
                  <div style={{
                    padding: '0.35rem 0.8rem',
                    fontSize: '0.72rem',
                    color: '#94a3b8',
                    backgroundColor: 'rgba(255, 255, 255, 0.04)',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
                    fontFamily: 'monospace',
                    display: 'flex',
                    justifyContent: 'space-between',
                  }}>
                    <span>Code Snippet</span>
                    <span style={{ textTransform: 'uppercase' }}>{lang}</span>
                  </div>
                  <pre style={{
                    margin: 0,
                    padding: '1rem',
                    fontSize: '0.88rem',
                    fontFamily: 'Consolas, Monaco, monospace',
                    color: '#e2e8f0',
                    overflowX: 'auto',
                    lineHeight: '1.5',
                  }}>
                    <code>{code}</code>
                  </pre>
                </div>
              );
            }
            return <p key={idx} style={{ margin: 0, whiteSpace: 'pre-line' }}>{part}</p>;
          })}
        </div>
      );
    }
    return <div style={{ whiteSpace: 'pre-line' }}>{content}</div>;
  };

  // ── Render Loading ──────────────────────────────────────────────────────────
  if (mode === 'LOADING') {
    return (
      <div style={{ padding: '6rem 2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        <div style={{
          width: '56px', height: '56px', borderRadius: '16px',
          background: theme.bg, border: `1px solid ${theme.border}`,
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          color: theme.color, marginBottom: '1.2rem',
        }}>
          <ShieldCheck size={32} />
        </div>
        <h3 style={{ fontSize: '1.25rem', color: 'var(--text-main)', marginBottom: '0.5rem' }}>
          Initializing Secure Examination Sandbox...
        </h3>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
          Configuring proctoring telemetry and loading questions for {meta?.title || 'Assessment'}
        </p>
      </div>
    );
  }

  // ── Render Start / Instructions Screen (META) ──────────────────────────────
  if (mode === 'META') {
    return (
      <div style={{ maxWidth: '720px', margin: '3rem auto', padding: '0 1.5rem' }}>
        <div className="card" style={{ padding: '2.5rem', border: `1px solid ${theme.border}` }}>
          
          {/* Company Pattern Header Banner */}
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.4rem 1rem',
              borderRadius: '20px',
              backgroundColor: theme.bg,
              border: `1px solid ${theme.border}`,
              color: theme.color,
              fontSize: '0.85rem',
              fontWeight: 700,
              marginBottom: '1rem',
            }}>
              <span>{theme.emoji}</span>
              <span>{theme.badge}</span>
            </div>

            <h1 style={{ fontSize: '1.75rem', marginBottom: '0.5rem', color: 'var(--text-main)' }}>
              {meta?.title || 'Technical Assessment'}
            </h1>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
              Candidate: <strong style={{ color: 'var(--text-main)' }}>{meta?.candidate_name || meta?.candidate_email}</strong> ({meta?.candidate_email})
            </p>
          </div>

          {error && (
            <div className="alert alert-error" style={{ marginBottom: '1.5rem' }}>
              <AlertTriangle size={16} /> <span>{error}</span>
            </div>
          )}

          {/* Assessment Specifications & Rules */}
          <div style={{
            padding: '1.4rem',
            borderRadius: '10px',
            backgroundColor: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--border-color)',
            marginBottom: '1.8rem',
            fontSize: '0.9rem',
          }}>
            <h4 style={{ marginBottom: '0.8rem', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Layers size={18} color={theme.color} /> Examination Structure & Duration
            </h4>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.8rem', marginBottom: '1.2rem' }}>
              <div style={{ padding: '0.75rem', borderRadius: '8px', backgroundColor: 'rgba(255, 255, 255, 0.03)', textAlign: 'center' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>QUESTIONS</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-main)' }}>{meta?.total_questions || 0}</div>
              </div>
              <div style={{ padding: '0.75rem', borderRadius: '8px', backgroundColor: 'rgba(255, 255, 255, 0.03)', textAlign: 'center' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>DURATION</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-main)' }}>{meta?.duration_minutes}m</div>
              </div>
              <div style={{ padding: '0.75rem', borderRadius: '8px', backgroundColor: 'rgba(255, 255, 255, 0.03)', textAlign: 'center' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>SECTION LOCK</div>
                <div style={{ fontSize: '0.88rem', fontWeight: 700, color: meta?.allow_section_switching ? 'var(--success)' : '#f87171', marginTop: '0.2rem' }}>
                  {meta?.allow_section_switching ? 'Flexible' : 'Sequential'}
                </div>
              </div>
            </div>

            {/* Pattern-specific Guidelines */}
            <div style={{
              padding: '0.9rem 1rem',
              borderRadius: '8px',
              backgroundColor: theme.bg,
              border: `1px solid ${theme.border}`,
              marginBottom: '1rem',
            }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, color: theme.color, marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <Sparkles size={14} /> {theme.name} Guidelines:
              </div>
              <ul style={{ paddingLeft: '1.2rem', margin: 0, fontSize: '0.82rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                {theme.guidance.map((rule, i) => (
                  <li key={i}>{rule}</li>
                ))}
              </ul>
            </div>

            <ul style={{ paddingLeft: '1.2rem', display: 'flex', flexDirection: 'column', gap: '0.4rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              <li>All responses are automatically saved in real-time to the cloud database.</li>
              <li>Once you click "Accept Terms & Begin", the non-pausable timer begins immediately.</li>
            </ul>
          </div>

          {/* System Check & Proctoring Consent */}
          <div style={{
            padding: '1.4rem',
            borderRadius: '10px',
            backgroundColor: 'rgba(99, 102, 241, 0.05)',
            border: '1px solid rgba(99, 102, 241, 0.25)',
            marginBottom: '1.8rem',
          }}>
            <h4 style={{ fontSize: '0.95rem', marginBottom: '0.6rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#c4b5fd' }}>
              <Camera size={18} /> System Check & Anti-Cheat Proctoring Consent
            </h4>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem', lineHeight: '1.4' }}>
              To ensure fairness and integrity for company recruitment, this test portal monitors webcam identity, browser focus, clipboard activity, and audio levels.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', fontSize: '0.84rem' }}>
              {meta?.proctoring_mode !== 'LOW_FRICTION' && (
                <>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={cameraConsent}
                      onChange={(e) => setCameraConsent(e.target.checked)}
                    />
                    <span>I consent to webcam identity verification & presence monitoring.</span>
                  </label>

                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={audioConsent}
                      onChange={(e) => setAudioConsent(e.target.checked)}
                    />
                    <span>I consent to acoustic background noise monitoring.</span>
                  </label>
                </>
              )}

              <label style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={monitoringConsent}
                  onChange={(e) => setMonitoringConsent(e.target.checked)}
                />
                <span>I understand that leaving the test window or pasting external code will log a security alert.</span>
              </label>
            </div>
          </div>

          <button
            onClick={handleStartExam}
            className="btn btn-primary"
            style={{ width: '100%', padding: '0.95rem', fontSize: '1.05rem', fontWeight: 700 }}
          >
            <Play size={18} /> Accept Terms & Begin Assessment
          </button>
        </div>
      </div>
    );
  }

  // ── Render Completed Screen ────────────────────────────────────────────────
  if (mode === 'COMPLETED') {
    return (
      <div style={{ maxWidth: '620px', margin: '4rem auto', padding: '0 1.5rem' }}>
        <div className="card" style={{ padding: '2.5rem', textAlign: 'center', border: `1px solid ${theme.border}` }}>
          
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.35rem 0.9rem',
            borderRadius: '20px',
            backgroundColor: theme.bg,
            border: `1px solid ${theme.border}`,
            color: theme.color,
            fontSize: '0.8rem',
            fontWeight: 700,
            marginBottom: '1.2rem',
          }}>
            <span>{theme.emoji}</span>
            <span>{theme.badge} Complete</span>
          </div>

          <div style={{
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            backgroundColor: submissionResult?.passed ? 'rgba(16, 185, 129, 0.15)' : 'rgba(99, 102, 241, 0.15)',
            color: submissionResult?.passed ? 'var(--success)' : 'var(--primary)',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '1.2rem',
          }}>
            <Award size={36} />
          </div>

          <h2 style={{ fontSize: '1.75rem', marginBottom: '0.4rem' }}>Assessment Completed!</h2>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '1.8rem' }}>
            Your responses have been securely submitted and verified by the automated evaluation engine.
          </p>

          <div style={{
            padding: '1.8rem',
            borderRadius: '12px',
            backgroundColor: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--border-color)',
            marginBottom: '2rem',
          }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>Final Evaluated Score</div>
            <div style={{ fontSize: '2.8rem', fontWeight: 800, color: submissionResult?.passed ? 'var(--success)' : 'var(--text-main)' }}>
              {submissionResult?.percentage}%
            </div>
            <div style={{ fontSize: '0.95rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>
              {submissionResult?.total_score} of {submissionResult?.max_score} points earned
            </div>

            <div style={{
              display: 'flex',
              justifyContent: 'center',
              gap: '1.5rem',
              marginTop: '1.2rem',
              paddingTop: '1.2rem',
              borderTop: '1px solid var(--border-color)',
              fontSize: '0.85rem',
            }}>
              <div>
                <span style={{ color: 'var(--text-dim)' }}>Status: </span>
                <strong style={{ color: submissionResult?.passed ? 'var(--success)' : '#f87171' }}>
                  {submissionResult?.passed ? 'PASSED' : 'COMPLETED'}
                </strong>
              </div>
              <div>
                <span style={{ color: 'var(--text-dim)' }}>Integrity Trust: </span>
                <strong style={{ color: integrityScore >= 80 ? 'var(--success)' : 'var(--warning)' }}>
                  {integrityScore.toFixed(0)}%
                </strong>
              </div>
            </div>
          </div>

          <p style={{ fontSize: '0.85rem', color: 'var(--text-dim)' }}>
            The recruiting and evaluation team has received your submission receipt. You may now close this window.
          </p>
        </div>
      </div>
    );
  }

  // ── Render Active Runner Screen ───────────────────────────────────────────
  const currentQ = session.questions[currentIndex];
  const answeredCount = Object.keys(answers).length;
  const isLastQuestion = currentIndex === session.questions.length - 1;
  const isUrgentTimer = secondsRemaining < 180;

  // Filtered questions for navigator if user selected a section filter
  const filteredQuestions = session.questions.map((q: any, originalIndex: number) => ({ q, originalIndex })).filter((item: any) => {
    if (selectedSectionFilter === 'ALL') return true;
    return (item.q.section_name || 'General') === selectedSectionFilter;
  });

  return (
    <div style={{ maxWidth: '1240px', margin: '1.5rem auto', padding: '0 1.5rem' }}>
      
      {/* Top Runner Header Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.9rem 1.4rem',
        borderRadius: '12px',
        backgroundColor: 'rgba(17, 24, 39, 0.95)',
        backdropFilter: 'blur(12px)',
        border: `1px solid ${theme.border}`,
        marginBottom: '1.5rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.25rem 0.7rem',
            borderRadius: '6px',
            fontSize: '0.78rem',
            fontWeight: 700,
            backgroundColor: theme.bg,
            color: theme.color,
            border: `1px solid ${theme.border}`,
          }}>
            {theme.emoji} {theme.badge}
          </span>

          <div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>{session.title}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <span>Question {currentIndex + 1} of {session.questions.length}</span>
              <span>•</span>
              <span style={{ color: 'var(--success)' }}>{saveStatus}</span>
              {!session.allow_section_switching && (
                <>
                  <span>•</span>
                  <span style={{ color: '#f87171', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <Lock size={11} /> Sequential Section Lock
                  </span>
                </>
              )}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1.2rem' }}>
          {/* Live Synchronized Timer */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.5rem 1rem',
            borderRadius: '8px',
            backgroundColor: isUrgentTimer ? 'rgba(239, 68, 68, 0.15)' : 'rgba(99, 102, 241, 0.15)',
            border: `1px solid ${isUrgentTimer ? 'rgba(239, 68, 68, 0.4)' : 'rgba(99, 102, 241, 0.4)'}`,
            color: isUrgentTimer ? 'var(--danger)' : 'var(--primary)',
            fontWeight: 800,
            fontSize: '1.1rem',
            fontFamily: 'monospace',
          }}>
            <Clock size={18} /> {formatTime(secondsRemaining)}
          </div>

          <button
            onClick={() => setShowSubmitModal(true)}
            className="btn btn-primary btn-sm"
            style={{ fontWeight: 600 }}
          >
            <Send size={15} /> Finish & Submit
          </button>
        </div>
      </div>

      {/* Proctoring Warning Banner */}
      {proctorWarning && (
        <div
          className="alert alert-error"
          style={{
            marginBottom: '1.2rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            color: '#f87171',
            padding: '0.75rem 1rem',
            borderRadius: '8px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertTriangle size={18} />
            <span>{proctorWarning}</span>
          </div>
          <button
            onClick={() => setProctorWarning(null)}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#f87171',
              cursor: 'pointer',
              fontWeight: 'bold',
            }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Main Runner Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '1.5rem', alignItems: 'start' }}>
        
        {/* Left Area: Active Question Box */}
        <div className="card" style={{ padding: '2rem' }}>
          
          {/* Section & Question Metadata Header */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.2rem', paddingBottom: '0.8rem', borderBottom: '1px solid var(--border-color)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
              <span className="badge badge-primary" style={{ fontWeight: 800 }}>Q{currentIndex + 1}</span>
              
              {/* Active Section Tag */}
              <span style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                padding: '0.2rem 0.6rem',
                borderRadius: '6px',
                backgroundColor: 'rgba(167, 139, 250, 0.15)',
                color: '#c4b5fd',
                border: '1px solid rgba(167, 139, 250, 0.3)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
              }}>
                <Layers size={13} /> {currentQ.section_name || 'General Section'}
              </span>

              <span className="badge badge-secondary">{currentQ.difficulty || 'Medium'}</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{currentQ.points} Points</span>
            </div>

            <button
              onClick={() => toggleMarkForReview(currentIndex)}
              className="btn btn-secondary btn-sm"
              style={{
                fontSize: '0.75rem',
                color: markedForReview.has(currentIndex) ? 'var(--warning)' : 'var(--text-muted)',
                borderColor: markedForReview.has(currentIndex) ? 'var(--warning)' : 'var(--border-color)',
              }}
            >
              <Bookmark size={14} /> {markedForReview.has(currentIndex) ? 'Marked for Review' : 'Mark for Review'}
            </button>
          </div>

          <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: 'var(--text-main)', lineHeight: '1.4' }}>
            {currentQ.title}
          </h3>

          {/* Formatted Question Body */}
          <div style={{
            fontSize: '0.98rem',
            lineHeight: '1.6',
            color: 'var(--text-main)',
            backgroundColor: 'rgba(255, 255, 255, 0.02)',
            padding: '1.3rem',
            borderRadius: '10px',
            border: '1px solid var(--border-color)',
            marginBottom: '1.6rem',
          }}>
            {renderQuestionContent(currentQ.content_markdown)}
          </div>

          {/* Option Choices */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', marginBottom: '2rem' }}>
            {currentQ.options.map((opt: any, optIndex: number) => {
              const isSelected = answers[currentQ.id]?.includes(opt.id);
              const optionLetters = ['A', 'B', 'C', 'D', 'E', 'F'];
              const letter = optionLetters[optIndex] || `${optIndex + 1}`;

              return (
                <div
                  key={opt.id}
                  onClick={() => handleSelectOption(currentQ.id, opt.id)}
                  style={{
                    padding: '1rem 1.2rem',
                    borderRadius: '10px',
                    backgroundColor: isSelected ? 'rgba(99, 102, 241, 0.16)' : 'rgba(255, 255, 255, 0.02)',
                    border: `1px solid ${isSelected ? 'var(--primary)' : 'var(--border-color)'}`,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '1rem',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    border: `2px solid ${isSelected ? 'var(--primary)' : 'var(--border-color)'}`,
                    backgroundColor: isSelected ? 'var(--primary)' : 'transparent',
                    color: isSelected ? '#FFF' : 'var(--text-muted)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 700,
                    fontSize: '0.85rem',
                    flexShrink: 0,
                  }}>
                    {isSelected ? '✓' : letter}
                  </div>
                  <span style={{ fontSize: '0.95rem', color: isSelected ? '#FFF' : 'var(--text-main)', lineHeight: '1.4' }}>
                    {opt.option_text}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Bottom Navigation */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
            <button
              onClick={() => setCurrentIndex((prev) => Math.max(0, prev - 1))}
              className="btn btn-secondary"
              disabled={currentIndex === 0}
            >
              <ChevronLeft size={16} /> Previous
            </button>

            {isLastQuestion ? (
              <button
                onClick={() => setShowSubmitModal(true)}
                className="btn btn-primary"
                style={{ fontWeight: 700 }}
              >
                Review & Submit <Send size={16} />
              </button>
            ) : (
              <button
                onClick={() => setCurrentIndex((prev) => Math.min(session.questions.length - 1, prev + 1))}
                className="btn btn-primary"
                style={{ fontWeight: 600 }}
              >
                Next Question <ChevronRight size={16} />
              </button>
            )}
          </div>
        </div>

        {/* Right Area: Sensory Proctoring & Question Navigator */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          
          {/* Live Anti-Cheat Telemetry Widget */}
          <div className="card" style={{ padding: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
              <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <Camera size={14} color="var(--primary)" /> {meta?.proctoring_mode === 'LOW_FRICTION' ? 'Behavioral Telemetry' : 'Live Proctor Stream'}
              </span>
              <span className="badge badge-success" style={{ fontSize: '0.6rem', padding: '0.1rem 0.45rem' }}>
                ACTIVE
              </span>
            </div>

            {/* Webcam / Feed Simulation Box */}
            <div style={{
              width: '100%', height: '110px', borderRadius: '8px',
              backgroundColor: '#0a0d14', border: '1px solid rgba(99, 102, 241, 0.3)',
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
              position: 'relative', overflow: 'hidden',
            }}>
              <Eye size={28} color="var(--primary)" style={{ opacity: 0.8, marginBottom: '0.2rem' }} />
              <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', textAlign: 'center', padding: '0 0.5rem' }}>
                {meta?.proctoring_mode === 'LOW_FRICTION' ? 'Browser Environment Monitored' : 'Candidate Presence Verified'}
              </div>

              {/* Blinking Live Indicator */}
              <div style={{
                position: 'absolute', top: '8px', right: '8px',
                width: '8px', height: '8px', borderRadius: '50%',
                backgroundColor: 'var(--success)', boxShadow: '0 0 8px var(--success)',
              }} />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.6rem', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              <span>Focus: Active</span>
              <span style={{ color: 'var(--primary)', fontWeight: 700 }}>Integrity: {integrityScore.toFixed(0)}%</span>
            </div>
          </div>

          {/* Question Navigator with Section Grouping */}
          <div className="card" style={{ padding: '1.2rem' }}>
            <h4 style={{ fontSize: '0.95rem', marginBottom: '0.8rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span>Question Palette</span>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                {answeredCount}/{session.questions.length} answered
              </span>
            </h4>

            {/* Section Filter Tabs if multi-section test */}
            {sectionsList.length > 1 && (
              <div style={{ display: 'flex', gap: '0.35rem', marginBottom: '0.9rem', flexWrap: 'wrap' }}>
                <button
                  onClick={() => setSelectedSectionFilter('ALL')}
                  style={{
                    padding: '0.25rem 0.55rem',
                    borderRadius: '4px',
                    fontSize: '0.7rem',
                    fontWeight: 600,
                    border: '1px solid var(--border-color)',
                    backgroundColor: selectedSectionFilter === 'ALL' ? 'var(--primary)' : 'rgba(255, 255, 255, 0.03)',
                    color: selectedSectionFilter === 'ALL' ? '#FFF' : 'var(--text-muted)',
                    cursor: 'pointer',
                  }}
                >
                  All Sections
                </button>
                {sectionsList.map((sec) => (
                  <button
                    key={sec}
                    onClick={() => setSelectedSectionFilter(sec)}
                    style={{
                      padding: '0.25rem 0.55rem',
                      borderRadius: '4px',
                      fontSize: '0.7rem',
                      fontWeight: 600,
                      border: '1px solid var(--border-color)',
                      backgroundColor: selectedSectionFilter === sec ? 'var(--primary)' : 'rgba(255, 255, 255, 0.03)',
                      color: selectedSectionFilter === sec ? '#FFF' : 'var(--text-muted)',
                      cursor: 'pointer',
                      maxWidth: '120px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                    title={sec}
                  >
                    {sec.replace('Part A: ', '').replace('Part B: ', '')}
                  </button>
                ))}
              </div>
            )}

            {/* Question Matrix */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '0.5rem', marginBottom: '1.2rem' }}>
              {filteredQuestions.map(({ q, originalIndex }: any) => {
                const isAnswered = !!answers[q.id]?.length;
                const isCurrent = originalIndex === currentIndex;
                const isReviewed = markedForReview.has(originalIndex);

                let bg = 'rgba(255, 255, 255, 0.03)';
                let border = 'var(--border-color)';
                if (isCurrent) {
                  border = 'var(--primary)';
                  bg = 'rgba(99, 102, 241, 0.25)';
                } else if (isAnswered) {
                  bg = 'rgba(16, 185, 129, 0.2)';
                  border = 'rgba(16, 185, 129, 0.5)';
                }
                if (isReviewed) {
                  border = 'var(--warning)';
                }

                return (
                  <button
                    key={q.id}
                    onClick={() => setCurrentIndex(originalIndex)}
                    style={{
                      padding: '0.55rem 0',
                      borderRadius: '6px',
                      backgroundColor: bg,
                      border: `1px solid ${border}`,
                      color: '#FFF',
                      fontWeight: isCurrent ? 800 : 500,
                      fontSize: '0.85rem',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    {originalIndex + 1}
                  </button>
                );
              })}
            </div>

            {/* Legend */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.74rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border-color)', paddingTop: '0.8rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                <div style={{ width: '10px', height: '10px', borderRadius: '2px', backgroundColor: 'rgba(16, 185, 129, 0.5)' }} />
                <span>Answered ({answeredCount})</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                <div style={{ width: '10px', height: '10px', borderRadius: '2px', backgroundColor: 'rgba(255, 255, 255, 0.05)', border: '1px solid var(--border-color)' }} />
                <span>Unanswered ({session.questions.length - answeredCount})</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                <div style={{ width: '10px', height: '10px', borderRadius: '2px', backgroundColor: 'var(--warning)' }} />
                <span>Marked for Review ({markedForReview.size})</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Submit Confirmation Modal */}
      {showSubmitModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.75)', backdropFilter: 'blur(6px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '1rem',
        }}>
          <div className="card" style={{ maxWidth: '440px', width: '100%', padding: '2rem', border: `1px solid ${theme.border}` }}>
            <h3 style={{ marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span>{theme.emoji}</span> Final Exam Submission
            </h3>
            <p style={{ fontSize: '0.85rem', marginBottom: '1.2rem', color: 'var(--text-muted)' }}>
              You have answered <strong>{answeredCount} of {session.questions.length}</strong> questions.
            </p>

            {answeredCount < session.questions.length && (
              <div className="alert alert-error" style={{ fontSize: '0.8rem', marginBottom: '1.2rem' }}>
                <AlertTriangle size={14} /> You have {session.questions.length - answeredCount} unanswered questions remaining.
              </div>
            )}

            <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.2rem' }}>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ flex: 1 }}
                onClick={() => setShowSubmitModal(false)}
              >
                Return to Test
              </button>
              <button
                type="button"
                className="btn btn-primary"
                style={{ flex: 1, fontWeight: 700 }}
                onClick={handleSubmitExam}
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Submitting...' : 'Confirm Submit'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
