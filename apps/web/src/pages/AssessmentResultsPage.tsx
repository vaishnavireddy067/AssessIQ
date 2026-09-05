import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiRequest } from '../api/client';
import { 
  ArrowLeft, Users, Award, CheckCircle2, XCircle, 
  Clock, Eye, FileText, ChevronRight, Sparkles, Shield, AlertTriangle, Download 
} from 'lucide-react';

export const AssessmentResultsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [assessment, setAssessment] = useState<any | null>(null);
  const [attempts, setAttempts] = useState<any[]>([]);
  const [selectedAttemptId, setSelectedAttemptId] = useState<string | null>(null);
  const [scorecard, setScorecard] = useState<any | null>(null);
  const [aiSummary, setAiSummary] = useState<any | null>(null);
  const [proctoringReport, setProctoringReport] = useState<any | null>(null);
  const [isLoadingScorecard, setIsLoadingScorecard] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const loadResults = async () => {
      try {
        setIsLoading(true);
        const assRes = await apiRequest(`/assessments/${id}`);
        setAssessment(assRes);

        const attRes = await apiRequest(`/assessments/${id}/results`);
        setAttempts(attRes);
      } catch (err) {
        console.error('Failed to load assessment results:', err);
      } finally {
        setIsLoading(false);
      }
    };
    loadResults();
  }, [id]);

  const [skillMatrix, setSkillMatrix] = useState<any | null>(null);

  const handleOpenScorecard = async (attemptId: string) => {
    setSelectedAttemptId(attemptId);
    setIsLoadingScorecard(true);
    setAiSummary(null);
    setProctoringReport(null);
    setSkillMatrix(null);
    try {
      const [res, aiRes, proctorRes, skillRes] = await Promise.allSettled([
        apiRequest(`/results/${attemptId}`),
        apiRequest(`/results/${attemptId}/ai-summary`),
        apiRequest(`/results/${attemptId}/proctoring`),
        apiRequest(`/results/${attemptId}/skill-matrix`),
      ]);
      if (res.status === 'fulfilled') setScorecard(res.value);
      if (aiRes.status === 'fulfilled') setAiSummary(aiRes.value);
      if (proctorRes.status === 'fulfilled') setProctoringReport(proctorRes.value);
      if (skillRes.status === 'fulfilled') setSkillMatrix(skillRes.value);
    } catch (err) {
      alert('Failed to load detailed scorecard');
    } finally {
      setIsLoadingScorecard(false);
    }
  };

  const totalCandidates = attempts.length;
  const passedCandidates = attempts.filter((a) => a.passed).length;
  const passRate = totalCandidates > 0 ? Math.round((passedCandidates / totalCandidates) * 100) : 0;

  if (isLoading) {
    return (
      <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        Loading assessment results & scores...
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '2rem auto', padding: '0 1.5rem' }}>
      {/* Top Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button onClick={() => navigate('/assessments')} className="btn btn-secondary btn-sm">
            <ArrowLeft size={16} /> All Assessments
          </button>
          <div>
            <h1 style={{ fontSize: '1.75rem', marginBottom: '0.2rem' }}>Results: {assessment?.title}</h1>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Passing Threshold: {assessment?.passing_score_percentage}% • {assessment?.duration_minutes} Mins
            </p>
          </div>
        </div>

        <a
          href={`/api/v1/admin/assessments/${id}/export`}
          target="_blank"
          rel="noreferrer"
          className="btn btn-secondary btn-sm"
          style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
        >
          <Download size={15} /> Export Cohort (CSV)
        </a>
      </div>

      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
        <div className="card">
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>Candidates Evaluated</div>
          <div style={{ fontSize: '2rem', fontWeight: 800 }}>{totalCandidates}</div>
        </div>
        <div className="card">
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>Passed Candidates</div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--success)' }}>{passedCandidates}</div>
        </div>
        <div className="card">
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>Pass Rate</div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--primary)' }}>{passRate}%</div>
        </div>
      </div>

      {/* Results Table */}
      <div className="card">
        <h3 style={{ fontSize: '1.2rem', marginBottom: '1.2rem' }}>Candidate Submissions</h3>

        {attempts.length === 0 ? (
          <div style={{ padding: '3rem 1rem', textAlign: 'center', color: 'var(--text-dim)' }}>
            No candidate attempts recorded yet for this assessment.
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Candidate</th>
                  <th>Status</th>
                  <th>Score</th>
                  <th>Percentage</th>
                  <th>Outcome</th>
                  <th>Submitted At</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {attempts.map((att) => (
                  <tr key={att.id}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{att.candidate_email}</div>
                      {/* Phase 9: AI Rationale inline summary */}
                      {att.ai_ranking_rationale && (
                        <div style={{
                          fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '0.2rem',
                          fontStyle: 'italic', maxWidth: '220px', lineHeight: 1.3,
                        }}>
                          ✨ {att.ai_ranking_rationale}
                        </div>
                      )}
                    </td>
                    <td>
                      <span className="badge badge-primary" style={{ fontSize: '0.65rem' }}>
                        {att.status}
                      </span>
                    </td>
                    <td style={{ fontWeight: 700 }}>
                      {att.total_score} / {att.max_score} pts
                    </td>
                    <td style={{ fontWeight: 700, color: att.passed ? 'var(--success)' : 'var(--danger)' }}>
                      {att.percentage}%
                    </td>
                    <td>
                      <span className={`badge ${att.passed ? 'badge-success' : 'badge-danger'}`}>
                        {att.passed ? 'PASSED' : 'FAILED'}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {att.submitted_at ? new Date(att.submitted_at).toLocaleString() : 'In Progress'}
                    </td>
                    <td>
                      <button
                        onClick={() => handleOpenScorecard(att.id)}
                        className="btn btn-secondary btn-sm"
                      >
                        <Eye size={14} /> Scorecard
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Detailed Scorecard Modal */}
      {selectedAttemptId && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.75)', backdropFilter: 'blur(8px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '1rem',
        }}>
          <div className="card" style={{ maxWidth: '750px', width: '100%', maxHeight: '90vh', overflowY: 'auto', padding: '2rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
              <div>
                <h3 style={{ fontSize: '1.3rem', marginBottom: '0.2rem' }}>Candidate Scorecard</h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  {scorecard?.candidate_email} • {scorecard?.assessment_title}
                </p>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <a
                  href={`/api/v1/admin/results/${selectedAttemptId}/export`}
                  target="_blank"
                  rel="noreferrer"
                  className="btn btn-secondary btn-sm"
                  style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
                >
                  <Download size={15} /> Export Scorecard (CSV)
                </a>
                <button
                  onClick={() => { setSelectedAttemptId(null); setScorecard(null); }}
                  className="btn btn-secondary btn-sm"
                >
                  Close
                </button>
              </div>
            </div>

            {isLoadingScorecard || !scorecard ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                Loading scorecard metrics...
              </div>
            ) : (
              <div>
                {/* Score Summary Box */}
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '1.2rem',
                  borderRadius: '10px',
                  backgroundColor: scorecard.passed ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                  border: `1px solid ${scorecard.passed ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                  marginBottom: '1.5rem',
                }}>
                  <div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Final Evaluation</div>
                    <div style={{ fontSize: '1.6rem', fontWeight: 800, color: scorecard.passed ? 'var(--success)' : 'var(--danger)' }}>
                      {scorecard.percentage}% ({scorecard.total_score} / {scorecard.max_score} Points)
                    </div>
                  </div>
                  <span className={`badge ${scorecard.passed ? 'badge-success' : 'badge-danger'}`} style={{ fontSize: '0.9rem', padding: '0.4rem 0.8rem' }}>
                    {scorecard.passed ? 'PASSED TEST' : 'DID NOT PASS'}
                  </span>
                </div>

                {/* Phase 9: Explainable AI Ranking Rationale */}
                {scorecard?.ai_ranking_rationale && (
                  <div style={{
                    padding: '1.1rem 1.3rem',
                    borderRadius: '10px',
                    backgroundColor: 'rgba(99, 102, 241, 0.07)',
                    border: '1px solid rgba(99, 102, 241, 0.2)',
                    marginBottom: '1.5rem',
                    display: 'flex',
                    gap: '0.8rem',
                    alignItems: 'flex-start',
                  }}>
                    <Sparkles size={18} color="var(--primary)" style={{ flexShrink: 0, marginTop: '2px' }} />
                    <div>
                      <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#c4b5fd', marginBottom: '0.3rem' }}>
                        ✨ AI RANKING RATIONALE
                      </div>
                      <div style={{ fontSize: '0.88rem', color: 'var(--text-main)', lineHeight: 1.5 }}>
                        {scorecard.ai_ranking_rationale}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '0.4rem' }}>
                        Advisory only — recruiter retains full hiring decision authority
                      </div>
                    </div>
                  </div>
                )}

                {/* AI Performance Analysis Card */}
                {aiSummary && (
                  <div style={{
                    padding: '1.2rem',
                    borderRadius: '10px',
                    backgroundColor: 'rgba(139, 92, 246, 0.08)',
                    border: '1px solid rgba(139, 92, 246, 0.3)',
                    marginBottom: '1.5rem',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.8rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Sparkles size={18} color="#8B5CF6" />
                        <span style={{ fontWeight: 700, fontSize: '1rem', color: '#c4b5fd' }}>AI Candidate Insights</span>
                      </div>
                      <span className={`badge ${
                        aiSummary.recommendation === 'STRONG_HIRE' ? 'badge-success' :
                        aiSummary.recommendation === 'HIRE' ? 'badge-primary' :
                        aiSummary.recommendation === 'BORDERLINE' ? 'badge-warning' : 'badge-danger'
                      }`} style={{ fontSize: '0.75rem', fontWeight: 700 }}>
                        {aiSummary.recommendation} • {aiSummary.technical_depth_rating}
                      </span>
                    </div>

                    <p style={{ fontSize: '0.85rem', lineHeight: '1.5', color: 'var(--text-main)', marginBottom: '0.8rem' }}>
                      {aiSummary.executive_summary}
                    </p>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                      {aiSummary.strengths?.length > 0 && (
                        <div>
                          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--success)', display: 'block', marginBottom: '0.3rem' }}>
                            Key Strengths
                          </span>
                          <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            {aiSummary.strengths.map((str: string, idx: number) => (
                              <li key={idx}>{str}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {aiSummary.weaknesses?.length > 0 && (
                        <div>
                          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#f87171', display: 'block', marginBottom: '0.3rem' }}>
                            Areas for Improvement
                          </span>
                          <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            {aiSummary.weaknesses.map((w: string, idx: number) => (
                              <li key={idx}>{w}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Integrity & Proctoring Audit Card */}
                {proctoringReport && (
                  <div style={{
                    padding: '1.2rem',
                    borderRadius: '10px',
                    backgroundColor: proctoringReport.is_flagged ? 'rgba(239, 68, 68, 0.08)' : 'rgba(16, 185, 129, 0.06)',
                    border: `1px solid ${proctoringReport.is_flagged ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.25)'}`,
                    marginBottom: '1.5rem',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.8rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Shield size={18} color={proctoringReport.is_flagged ? '#ef4444' : '#10b981'} />
                        <span style={{ fontWeight: 700, fontSize: '1rem', color: proctoringReport.is_flagged ? '#f87171' : '#34d399' }}>
                          Integrity & Proctoring Audit
                        </span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontSize: '0.85rem', fontWeight: 700 }}>
                          Trust Score: {proctoringReport.integrity_score}/100
                        </span>
                        <span className={`badge ${
                          proctoringReport.risk_level === 'NORMAL' ? 'badge-success' :
                          proctoringReport.risk_level === 'LOW_RISK' ? 'badge-primary' :
                          proctoringReport.risk_level === 'REVIEW_REQUIRED' ? 'badge-warning' : 'badge-danger'
                        }`} style={{ fontSize: '0.7rem' }}>
                          {proctoringReport.risk_level?.replace('_', ' ')}
                        </span>
                      </div>
                    </div>

                    {/* Telemetry Counter Grid */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '0.5rem', marginBottom: '1rem' }}>
                      <div style={{ backgroundColor: 'rgba(255,255,255,0.03)', padding: '0.4rem', borderRadius: '6px', textAlign: 'center' }}>
                        <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Tab Switches</div>
                        <div style={{ fontSize: '1rem', fontWeight: 700, color: proctoringReport.tab_switches_count > 0 ? '#f87171' : 'var(--text-main)' }}>
                          {proctoringReport.tab_switches_count}
                        </div>
                      </div>
                      <div style={{ backgroundColor: 'rgba(255,255,255,0.03)', padding: '0.4rem', borderRadius: '6px', textAlign: 'center' }}>
                        <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Fullscreen Exits</div>
                        <div style={{ fontSize: '1rem', fontWeight: 700, color: proctoringReport.fullscreen_exits_count > 0 ? '#f87171' : 'var(--text-main)' }}>
                          {proctoringReport.fullscreen_exits_count}
                        </div>
                      </div>
                      <div style={{ backgroundColor: 'rgba(255,255,255,0.03)', padding: '0.4rem', borderRadius: '6px', textAlign: 'center' }}>
                        <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Pastes</div>
                        <div style={{ fontSize: '1rem', fontWeight: 700, color: proctoringReport.paste_count > 0 ? '#f87171' : 'var(--text-main)' }}>
                          {proctoringReport.paste_count}
                        </div>
                      </div>
                      <div style={{ backgroundColor: 'rgba(255,255,255,0.03)', padding: '0.4rem', borderRadius: '6px', textAlign: 'center' }}>
                        <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Face Absent</div>
                        <div style={{ fontSize: '1rem', fontWeight: 700, color: proctoringReport.face_absence_count > 0 ? '#f87171' : 'var(--text-main)' }}>
                          {proctoringReport.face_absence_count || 0}
                        </div>
                      </div>
                      <div style={{ backgroundColor: 'rgba(255,255,255,0.03)', padding: '0.4rem', borderRadius: '6px', textAlign: 'center' }}>
                        <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Multi Faces</div>
                        <div style={{ fontSize: '1rem', fontWeight: 700, color: proctoringReport.multiple_faces_count > 0 ? '#f87171' : 'var(--text-main)' }}>
                          {proctoringReport.multiple_faces_count || 0}
                        </div>
                      </div>
                      <div style={{ backgroundColor: 'rgba(255,255,255,0.03)', padding: '0.4rem', borderRadius: '6px', textAlign: 'center' }}>
                        <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Audio Spikes</div>
                        <div style={{ fontSize: '1rem', fontWeight: 700, color: proctoringReport.audio_spikes_count > 0 ? '#f87171' : 'var(--text-main)' }}>
                          {proctoringReport.audio_spikes_count || 0}
                        </div>
                      </div>
                    </div>

                    {/* Transparent Deductions Breakdown */}
                    {proctoringReport.weighted_deductions_json?.length > 0 && (
                      <div style={{ marginBottom: '1rem', padding: '0.6rem 0.8rem', borderRadius: '6px', backgroundColor: 'rgba(0,0,0,0.2)' }}>
                        <span style={{ fontSize: '0.72rem', fontWeight: 600, color: '#f87171', display: 'block', marginBottom: '0.3rem' }}>
                          Explainable Deductions:
                        </span>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                          {proctoringReport.weighted_deductions_json.map((d: any, idx: number) => (
                            <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem' }}>
                              <span>{d.description} ({d.occurrences}x)</span>
                              <span style={{ color: '#f87171', fontWeight: 700 }}>-{d.points_deducted} pts ({d.severity})</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {proctoringReport.events?.length > 0 && (
                      <div>
                        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: '0.4rem' }}>
                          Security Event Timeline
                        </span>
                        <div style={{ maxHeight: '120px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                          {proctoringReport.events.map((evt: any) => (
                            <div key={evt.id} style={{
                              display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem',
                              padding: '0.3rem 0.5rem', borderRadius: '4px', backgroundColor: 'rgba(0,0,0,0.2)'
                            }}>
                              <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                                <span className={`badge ${
                                  evt.severity === 'CRITICAL' ? 'badge-danger' :
                                  evt.severity === 'HIGH' ? 'badge-danger' :
                                  evt.severity === 'MEDIUM' ? 'badge-warning' : 'badge-secondary'
                                }`} style={{ fontSize: '0.6rem', padding: '0.05rem 0.35rem' }}>
                                  {evt.severity}
                                </span>
                                <span style={{ color: '#FFF', fontWeight: 600 }}>{evt.event_type}</span>
                              </div>
                              <span style={{ color: 'var(--text-dim)' }}>{new Date(evt.timestamp).toLocaleTimeString()}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Candidate Multi-Skill Competency Matrix */}
                {skillMatrix && skillMatrix.skills?.length > 0 && (
                  <div style={{
                    padding: '1.2rem',
                    borderRadius: '10px',
                    backgroundColor: 'rgba(59, 130, 246, 0.06)',
                    border: '1px solid rgba(59, 130, 246, 0.25)',
                    marginBottom: '1.5rem',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Award size={18} color="#60a5fa" />
                        <span style={{ fontWeight: 700, fontSize: '1rem', color: '#93c5fd' }}>
                          Candidate Skill Competency Matrix
                        </span>
                      </div>
                      <span className="badge badge-primary" style={{ fontSize: '0.75rem', fontWeight: 700 }}>
                        Overall: {skillMatrix.overall_proficiency}
                      </span>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      {skillMatrix.skills.map((s: any, idx: number) => {
                        const isHigh = s.score_percentage >= 75;
                        const isMid = s.score_percentage >= 50;
                        const barColor = isHigh ? 'var(--success)' : isMid ? 'var(--primary)' : '#f87171';

                        return (
                          <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                              <span style={{ fontWeight: 600 }}>{s.skill}</span>
                              <span style={{ color: barColor, fontWeight: 700 }}>
                                {s.score_percentage}% ({s.points_earned} / {s.total_points_possible} pts) • {s.proficiency_level}
                              </span>
                            </div>
                            <div style={{
                              width: '100%', height: '7px', borderRadius: '4px',
                              backgroundColor: 'rgba(255, 255, 255, 0.06)', overflow: 'hidden'
                            }}>
                              <div style={{
                                width: `${s.score_percentage}%`,
                                height: '100%',
                                backgroundColor: barColor,
                                borderRadius: '4px',
                                transition: 'width 0.4s ease'
                              }} />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Question by Question Breakdown */}
                <h4 style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>Question Breakdown</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {scorecard.questions.map((q: any, i: number) => (
                    <div
                      key={q.question_id}
                      style={{
                        padding: '1rem',
                        borderRadius: '8px',
                        backgroundColor: 'rgba(255, 255, 255, 0.02)',
                        border: '1px solid var(--border-color)',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                        <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>
                          Q{i + 1}: {q.title}
                        </span>
                        <span className={`badge ${q.is_correct ? 'badge-success' : 'badge-danger'}`} style={{ fontSize: '0.65rem' }}>
                          {q.is_correct ? `+${q.score_awarded} pts` : `0 / ${q.points} pts`}
                        </span>
                      </div>

                      <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                        {q.content_markdown}
                      </p>

                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginBottom: '0.6rem' }}>
                        {q.options.map((opt: any) => {
                          const isSelectedByCandidate = q.selected_option_ids.includes(opt.id);
                          const isCorrect = opt.is_correct;

                          let bg = 'rgba(255, 255, 255, 0.02)';
                          let border = 'var(--border-color)';
                          if (isCorrect) {
                            bg = 'rgba(16, 185, 129, 0.1)';
                            border = 'rgba(16, 185, 129, 0.4)';
                          } else if (isSelectedByCandidate && !isCorrect) {
                            bg = 'rgba(239, 68, 68, 0.1)';
                            border = 'rgba(239, 68, 68, 0.4)';
                          }

                          return (
                            <div
                              key={opt.id}
                              style={{
                                padding: '0.5rem 0.75rem',
                                borderRadius: '6px',
                                backgroundColor: bg,
                                border: `1px solid ${border}`,
                                fontSize: '0.8rem',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                              }}
                            >
                              <span>{opt.option_text}</span>
                              <div style={{ display: 'flex', gap: '0.4rem' }}>
                                {isSelectedByCandidate && (
                                  <span className="badge badge-primary" style={{ fontSize: '0.6rem', padding: '0.1rem 0.35rem' }}>
                                    Candidate Pick
                                  </span>
                                )}
                                {isCorrect && (
                                  <span className="badge badge-success" style={{ fontSize: '0.6rem', padding: '0.1rem 0.35rem' }}>
                                    Correct Answer
                                  </span>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>

                      {q.explanation && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontStyle: 'italic' }}>
                          Explanation: {q.explanation}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
