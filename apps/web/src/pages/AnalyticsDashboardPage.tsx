import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiRequest } from '../api/client';
import {
  Shield, AlertTriangle, CheckCircle2, TrendingUp, Users,
  FileSearch, BarChart3, Star, Zap, Eye, ChevronDown, ChevronUp,
  RefreshCw, Send, Award, Briefcase, Lock
} from 'lucide-react';

type Tab = 'passport' | 'fairness' | 'leakradar' | 'panelreview' | 'outcomes';

export const AnalyticsDashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<Tab>('passport');
  const [loading, setLoading] = useState(false);

  // --- Passport State ---
  const [passport, setPassport] = useState<any | null>(null);

  // --- Fairness State ---
  const [assessmentId, setAssessmentId] = useState('');
  const [fairnessReport, setFairnessReport] = useState<any | null>(null);

  // --- Leak Radar State ---
  const [leakReport, setLeakReport] = useState<any | null>(null);

  // --- Panel Review State ---
  const [panelReviews, setPanelReviews] = useState<any[]>([]);
  const [voteModal, setVoteModal] = useState<{ reviewId: string; open: boolean } | null>(null);
  const [verdict, setVerdict] = useState('HIRE');
  const [voteNotes, setVoteNotes] = useState('');

  // --- Outcomes State ---
  const [outcomeReport, setOutcomeReport] = useState<any | null>(null);
  const [newOutcome, setNewOutcome] = useState({ attempt_id: '', performance_rating: 4, role_title: '', notes: '' });

  const loadPassport = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiRequest('/passport/me');
      setPassport(res);
    } catch { } finally { setLoading(false); }
  }, []);

  const loadLeakRadar = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiRequest('/questions/leak-radar');
      setLeakReport(res);
    } catch { } finally { setLoading(false); }
  }, []);

  const loadPanelReviews = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiRequest('/panel-reviews');
      setPanelReviews(res);
    } catch { } finally { setLoading(false); }
  }, []);

  const loadOutcomes = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiRequest('/outcomes/correlation');
      setOutcomeReport(res);
    } catch { } finally { setLoading(false); }
  }, []);

  useEffect(() => {
    if (activeTab === 'passport') loadPassport();
    if (activeTab === 'leakradar') loadLeakRadar();
    if (activeTab === 'panelreview') loadPanelReviews();
    if (activeTab === 'outcomes') loadOutcomes();
  }, [activeTab]);

  const handleFairnessLoad = async () => {
    if (!assessmentId.trim()) return;
    setLoading(true);
    try {
      const res = await apiRequest(`/assessments/${assessmentId.trim()}/fairness-audit`);
      setFairnessReport(res);
    } catch { alert('Failed to load fairness report'); } finally { setLoading(false); }
  };

  const handleTriggerScan = async () => {
    await apiRequest('/questions/leak-scan', { method: 'POST' });
    setTimeout(loadLeakRadar, 1500);
  };

  const handleCastVote = async () => {
    if (!voteModal) return;
    try {
      await apiRequest(`/panel-reviews/${voteModal.reviewId}/vote`, {
        method: 'POST',
        body: JSON.stringify({ verdict, notes: voteNotes }),
      });
      setVoteModal(null);
      setVoteNotes('');
      loadPanelReviews();
    } catch (e: any) { alert(e.message || 'Vote failed'); }
  };

  const handleSubmitOutcome = async () => {
    try {
      await apiRequest('/outcomes', {
        method: 'POST',
        body: JSON.stringify({
          attempt_id: newOutcome.attempt_id,
          performance_rating: newOutcome.performance_rating,
          role_title: newOutcome.role_title,
          notes: newOutcome.notes,
        }),
      });
      setNewOutcome({ attempt_id: '', performance_rating: 4, role_title: '', notes: '' });
      loadOutcomes();
    } catch (e: any) { alert(e.message || 'Failed to submit outcome'); }
  };

  const tabs: { key: Tab; label: string; icon: React.ReactNode }[] = [
    { key: 'passport', label: 'Skill Passport', icon: <Award size={16} /> },
    { key: 'fairness', label: 'Fairness Audit', icon: <BarChart3 size={16} /> },
    { key: 'leakradar', label: 'Leak Radar', icon: <FileSearch size={16} /> },
    { key: 'panelreview', label: 'Panel Review', icon: <Users size={16} /> },
    { key: 'outcomes', label: 'Post-Hire Loop', icon: <TrendingUp size={16} /> },
  ];

  return (
    <div style={{ maxWidth: '1100px', margin: '2rem auto', padding: '0 1.5rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800, marginBottom: '0.4rem' }}>
          ✨ Analytics & Differentiators
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          Phase 9 enterprise analytics — skill passports, fairness audits, leak radar, panel review, and post-hire outcomes.
        </p>
      </div>

      {/* Tab Bar */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={`btn btn-sm ${activeTab === t.key ? 'btn-primary' : 'btn-secondary'}`}
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {/* ── PASSPORT TAB ─────────────────────────────── */}
      {activeTab === 'passport' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>🎖 My Verified Skill Passport</h2>
            <button className="btn btn-secondary btn-sm" onClick={loadPassport} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <RefreshCw size={14} /> Refresh
            </button>
          </div>
          {loading && <p style={{ color: 'var(--text-muted)' }}>Loading passport...</p>}
          {passport && (
            <div className="card" style={{ padding: '2rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
                <div>
                  <div style={{ fontSize: '1.3rem', fontWeight: 800 }}>{passport.display_name || passport.candidate_email}</div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>{passport.candidate_email}</div>
                  <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    <span className="badge badge-primary">{passport.total_assessments_taken} Assessments Taken</span>
                    <span className={`badge ${passport.is_public ? 'badge-success' : 'badge-secondary'}`}>
                      {passport.is_public ? '🌐 Public' : '🔒 Private'}
                    </span>
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={async () => {
                      await apiRequest('/passport/me/visibility', { method: 'PATCH' });
                      loadPassport();
                    }}
                    style={{ marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
                  >
                    <Lock size={14} /> Toggle Visibility
                  </button>
                  {passport.is_public && (
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', wordBreak: 'break-all' }}>
                      Share link: /passport/public/{passport.share_token}
                    </div>
                  )}
                </div>
              </div>

              {/* Skill Bars */}
              {passport.skills && passport.skills.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {passport.skills.map((skill: any) => (
                    <div key={skill.skill_name}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                        <span style={{ fontWeight: 600, fontSize: '0.88rem' }}>{skill.skill_name}</span>
                        <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                          Best: <strong style={{ color: 'var(--success)' }}>{skill.best_score}%</strong> &nbsp;|&nbsp; Avg: {skill.avg_score}% &nbsp;|&nbsp; {skill.attempts_count} attempts
                        </span>
                      </div>
                      <div style={{ height: '8px', borderRadius: '99px', backgroundColor: 'rgba(255,255,255,0.08)' }}>
                        <div style={{
                          height: '100%', borderRadius: '99px', width: `${skill.avg_score}%`,
                          background: 'linear-gradient(90deg, var(--primary), #a78bfa)',
                          transition: 'width 0.8s ease',
                        }} />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                  No skill data yet. Complete tagged assessments to populate your passport.
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── FAIRNESS AUDIT TAB ───────────────────────── */}
      {activeTab === 'fairness' && (
        <div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '1rem' }}>⚖️ Fairness & Equivalence Audit</h2>
          <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
              Enter an Assessment ID to generate a statistical fairness report proving all candidates experienced equivalent difficulty — legally defensible for enterprise HR teams.
            </p>
            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
              <input
                type="text"
                className="input"
                placeholder="Assessment UUID..."
                value={assessmentId}
                onChange={e => setAssessmentId(e.target.value)}
                style={{ flex: 1, minWidth: '240px' }}
              />
              <button className="btn btn-primary btn-sm" onClick={handleFairnessLoad} disabled={loading} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <BarChart3 size={15} /> Generate Report
              </button>
            </div>
          </div>
          {fairnessReport && (
            <div className="card" style={{ padding: '1.5rem' }}>
              <div style={{
                padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem',
                backgroundColor: fairnessReport.is_statistically_fair ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                border: `1px solid ${fairnessReport.is_statistically_fair ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem' }}>
                  {fairnessReport.is_statistically_fair
                    ? <CheckCircle2 size={18} color="var(--success)" />
                    : <AlertTriangle size={18} color="var(--danger)" />}
                  <strong>{fairnessReport.is_statistically_fair ? 'Statistically Fair' : 'Variance Detected'}</strong>
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>{fairnessReport.fairness_summary}</p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
                {[
                  { label: 'Total Attempts', value: fairnessReport.total_attempts },
                  { label: 'Avg Score', value: `${fairnessReport.avg_score_pct}%` },
                  { label: 'Std Deviation', value: `σ = ${fairnessReport.std_deviation}` },
                ].map(m => (
                  <div key={m.label} className="card" style={{ padding: '1rem', textAlign: 'center' }}>
                    <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--primary)' }}>{m.value}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{m.label}</div>
                  </div>
                ))}
              </div>

              <h4 style={{ marginBottom: '0.75rem', fontSize: '0.9rem' }}>Per-Question Difficulty Breakdown</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {fairnessReport.question_difficulty_breakdown.map((q: any) => (
                  <div key={q.question_id} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '0.7rem 1rem', borderRadius: '8px',
                    backgroundColor: q.is_flagged ? 'rgba(239,68,68,0.08)' : 'rgba(255,255,255,0.03)',
                    border: `1px solid ${q.is_flagged ? 'rgba(239,68,68,0.25)' : 'rgba(255,255,255,0.06)'}`,
                  }}>
                    <span style={{ fontSize: '0.82rem', flex: 1 }}>{q.title}</span>
                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{q.correct_count}/{q.total_answers} correct</span>
                      <span style={{ fontWeight: 700, fontSize: '0.88rem', color: q.difficulty_observed_pct < 40 ? 'var(--danger)' : 'var(--success)' }}>
                        {q.difficulty_observed_pct}%
                      </span>
                      {q.is_flagged && <span className="badge badge-danger" style={{ fontSize: '0.6rem' }}>⚠️ Outlier</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── LEAK RADAR TAB ──────────────────────────── */}
      {activeTab === 'leakradar' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>🔍 Leak Radar — Question Integrity</h2>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button className="btn btn-secondary btn-sm" onClick={loadLeakRadar} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <RefreshCw size={14} /> Refresh
              </button>
              <button className="btn btn-primary btn-sm" onClick={handleTriggerScan} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <Zap size={14} /> Run Full Scan
              </button>
            </div>
          </div>
          {leakReport && (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
                {[
                  { label: 'Questions Checked', value: leakReport.total_questions_checked, color: 'var(--primary)' },
                  { label: 'High Risk Detected', value: leakReport.high_risk_count, color: 'var(--danger)' },
                ].map(m => (
                  <div key={m.label} className="card" style={{ padding: '1rem', textAlign: 'center' }}>
                    <div style={{ fontSize: '2rem', fontWeight: 800, color: m.color }}>{m.value}</div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{m.label}</div>
                  </div>
                ))}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {leakReport.questions.map((q: any) => (
                  <div key={q.question_id} style={{
                    padding: '1rem', borderRadius: '8px',
                    backgroundColor: q.leak_risk_score >= 75 ? 'rgba(239,68,68,0.07)' : q.leak_risk_score >= 50 ? 'rgba(245,158,11,0.07)' : 'rgba(255,255,255,0.03)',
                    border: `1px solid ${q.leak_risk_score >= 75 ? 'rgba(239,68,68,0.25)' : 'rgba(255,255,255,0.06)'}`,
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: '0.88rem' }}>{q.title}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                          Used {q.usage_count} times &nbsp;|&nbsp; Last checked: {q.leak_last_checked_at ? new Date(q.leak_last_checked_at).toLocaleDateString() : 'Never'}
                        </div>
                        <div style={{ fontSize: '0.78rem', marginTop: '0.4rem', fontStyle: 'italic', color: q.leak_risk_score >= 75 ? 'var(--danger)' : 'var(--text-muted)' }}>
                          {q.recommendation}
                        </div>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{
                          fontSize: '1.4rem', fontWeight: 800,
                          color: q.leak_risk_score >= 75 ? 'var(--danger)' : q.leak_risk_score >= 50 ? '#f59e0b' : 'var(--success)',
                        }}>
                          {q.leak_risk_score}
                        </div>
                        <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Leak Risk Score</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
          {!leakReport && !loading && (
            <div className="card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              Click "Refresh" to load Leak Radar data for your question bank.
            </div>
          )}
        </div>
      )}

      {/* ── PANEL REVIEW TAB ────────────────────────── */}
      {activeTab === 'panelreview' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>🗳 Panel Review — Borderline Candidates</h2>
            <button className="btn btn-secondary btn-sm" onClick={loadPanelReviews} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <RefreshCw size={14} /> Refresh
            </button>
          </div>
          {panelReviews.length === 0 && (
            <div className="card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              No panel reviews pending. Borderline candidates (55-75% score) are automatically queued here for multi-recruiter review.
            </div>
          )}
          {panelReviews.map((review: any) => (
            <div key={review.id} className="card" style={{ padding: '1.25rem', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.75rem' }}>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>
                    Attempt ID: <code style={{ fontSize: '0.7rem' }}>{review.attempt_id}</code>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <span className={`badge ${review.status === 'APPROVED' ? 'badge-success' : review.status === 'REJECTED' ? 'badge-danger' : 'badge-primary'}`}>
                      {review.status}
                    </span>
                    {review.final_verdict && (
                      <span style={{ fontSize: '0.8rem', fontWeight: 700, color: review.final_verdict === 'HIRE' ? 'var(--success)' : 'var(--danger)' }}>
                        → Final: {review.final_verdict}
                      </span>
                    )}
                  </div>
                  <div style={{ marginTop: '0.5rem', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    {review.votes_cast} / {review.required_votes} votes cast
                  </div>
                </div>
                {review.status === 'PENDING' && (
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={() => setVoteModal({ reviewId: review.id, open: true })}
                    style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
                  >
                    <Send size={14} /> Cast Vote
                  </button>
                )}
              </div>
              {review.votes.length > 0 && (
                <div style={{ marginTop: '0.75rem', borderTop: '1px solid rgba(255,255,255,0.07)', paddingTop: '0.75rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  {review.votes.map((v: any) => (
                    <div key={v.id} style={{
                      fontSize: '0.75rem', padding: '0.3rem 0.6rem', borderRadius: '6px',
                      backgroundColor: v.verdict === 'HIRE' ? 'rgba(16,185,129,0.15)' : v.verdict === 'REJECT' ? 'rgba(239,68,68,0.15)' : 'rgba(99,102,241,0.15)',
                      color: v.verdict === 'HIRE' ? 'var(--success)' : v.verdict === 'REJECT' ? 'var(--danger)' : 'var(--primary)',
                    }}>
                      {v.verdict} {v.notes && `— "${v.notes}"`}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* ── POST-HIRE OUTCOMES TAB ──────────────────── */}
      {activeTab === 'outcomes' && (
        <div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '1.5rem' }}>📈 Post-Hire Outcome Loop</h2>

          {/* Submit Outcome Form */}
          <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
            <h4 style={{ marginBottom: '1rem', fontSize: '0.95rem' }}>Record a New Performance Outcome</h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.4rem' }}>Attempt ID</label>
                <input className="input" placeholder="UUID of assessment attempt..." value={newOutcome.attempt_id}
                  onChange={e => setNewOutcome(p => ({ ...p, attempt_id: e.target.value }))} />
              </div>
              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.4rem' }}>Performance Rating (1-5)</label>
                <select className="input" value={newOutcome.performance_rating}
                  onChange={e => setNewOutcome(p => ({ ...p, performance_rating: parseInt(e.target.value) }))}>
                  {[1, 2, 3, 4, 5].map(r => <option key={r} value={r}>{r} — {['', 'Poor', 'Below Average', 'Average', 'Good', 'Exceptional'][r]}</option>)}
                </select>
              </div>
              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.4rem' }}>Role Title</label>
                <input className="input" placeholder="e.g. Senior Backend Engineer" value={newOutcome.role_title}
                  onChange={e => setNewOutcome(p => ({ ...p, role_title: e.target.value }))} />
              </div>
              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.4rem' }}>Notes (optional)</label>
                <input className="input" placeholder="e.g. Exceeded expectations in Q3..." value={newOutcome.notes}
                  onChange={e => setNewOutcome(p => ({ ...p, notes: e.target.value }))} />
              </div>
            </div>
            <button className="btn btn-primary btn-sm" onClick={handleSubmitOutcome} style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Briefcase size={14} /> Submit Outcome
            </button>
          </div>

          {/* Correlation Report */}
          {outcomeReport && (
            <div className="card" style={{ padding: '1.5rem' }}>
              <div style={{
                padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem',
                backgroundColor: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)',
              }}>
                <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#c4b5fd', marginBottom: '0.3rem' }}>📊 CORRELATION ANALYSIS</div>
                <p style={{ fontSize: '0.88rem', color: 'var(--text-main)', margin: 0 }}>{outcomeReport.correlation_summary}</p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
                {[
                  { label: 'Total Outcomes', value: outcomeReport.total_outcomes },
                  { label: 'Avg Assessment Score', value: `${outcomeReport.avg_assessment_score}%` },
                  { label: 'High Scorers Perf.', value: `${outcomeReport.high_scorers_avg_performance}/5` },
                  { label: 'Low Scorers Perf.', value: `${outcomeReport.low_scorers_avg_performance}/5` },
                ].map(m => (
                  <div key={m.label} className="card" style={{ padding: '0.75rem', textAlign: 'center' }}>
                    <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--primary)' }}>{m.value}</div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{m.label}</div>
                  </div>
                ))}
              </div>

              <h4 style={{ marginBottom: '0.75rem', fontSize: '0.88rem' }}>Individual Outcomes</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {outcomeReport.outcomes.map((o: any) => (
                  <div key={o.id} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '0.75rem 1rem', borderRadius: '8px',
                    backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)',
                    flexWrap: 'wrap', gap: '0.5rem',
                  }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{o.candidate_email}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{o.role_title} • {o.review_period_months}mo review</div>
                    </div>
                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Assessment: <strong>{o.assessment_score_pct}%</strong></span>
                      <div style={{ display: 'flex', gap: '2px' }}>
                        {[1, 2, 3, 4, 5].map(star => (
                          <Star key={star} size={14} fill={star <= o.performance_rating ? '#f59e0b' : 'none'} color="#f59e0b" />
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {!outcomeReport && !loading && (
            <div className="card" style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.88rem' }}>
              No outcomes recorded yet. Submit your first post-hire performance rating to start building the correlation dataset.
            </div>
          )}
        </div>
      )}

      {/* Vote Modal */}
      {voteModal?.open && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(6px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 200,
        }}>
          <div className="card" style={{ padding: '2rem', maxWidth: '420px', width: '100%' }}>
            <h3 style={{ marginBottom: '1.25rem' }}>🗳 Cast Your Vote</h3>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ fontSize: '0.82rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.4rem' }}>Verdict</label>
              <select className="input" value={verdict} onChange={e => setVerdict(e.target.value)}>
                <option value="HIRE">✅ HIRE</option>
                <option value="REJECT">❌ REJECT</option>
                <option value="NEEDS_MORE_INFO">⏸ NEEDS MORE INFO</option>
              </select>
            </div>
            <div style={{ marginBottom: '1.25rem' }}>
              <label style={{ fontSize: '0.82rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.4rem' }}>Notes (visible to other reviewers)</label>
              <textarea className="input" rows={3} placeholder="Add reasoning for your vote..."
                value={voteNotes} onChange={e => setVoteNotes(e.target.value)}
                style={{ resize: 'vertical' }} />
            </div>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button className="btn btn-primary" onClick={handleCastVote} style={{ flex: 1 }}>Submit Vote</button>
              <button className="btn btn-secondary" onClick={() => setVoteModal(null)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
