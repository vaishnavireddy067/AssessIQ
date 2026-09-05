import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiRequest } from '../api/client';
import { 
  Bot, Sparkles, Loader2, CheckCircle2, AlertTriangle, 
  Layers, ShieldAlert, Check, Plus, RefreshCw, ArrowRight, Zap, Target, BookmarkCheck
} from 'lucide-react';

const TEMPLATE_META: Record<string, { icon: string; name: string; tag: string }> = {
  CODING_ONLY: { icon: '🖥️', name: 'Coding-Only (DSA)', tag: 'Google / Amazon / Product-Style' },
  TECHNICAL_MCQ: { icon: '🧩', name: 'Technical Fundamentals + MCQ', tag: 'CS Core & Engineering' },
  APTITUDE_REASONING: { icon: '🧠', name: 'Aptitude & Logical Reasoning', tag: 'Analyst & Finance Roles' },
  VERBAL_APTITUDE: { icon: '🗣️', name: 'Verbal & Quantitative Aptitude', tag: 'Consulting & Non-Tech' },
  FULL_CAMPUS: { icon: '🎓', name: 'Full Campus / Tier-1 Drive', tag: 'TCS / Infosys / Wipro Style' },
  CUSTOM_BLANK: { icon: '✏️', name: 'Custom Architecture', tag: 'Bespoke Pattern' },
};

export const AssessmentCopilotPage: React.FC = () => {
  const navigate = useNavigate();
  const [roleTitle, setRoleTitle] = useState('Senior Backend Engineer');
  const [seniority, setSeniority] = useState('SENIOR');
  const [targetSkills, setTargetSkills] = useState('Python, PostgreSQL, Redis, Docker, System Design');
  const [durationMinutes, setDurationMinutes] = useState(60);
  const [includeCoding, setIncludeCoding] = useState(true);
  const [includeSql, setIncludeSql] = useState(true);
  const [mcqCount, setMcqCount] = useState(4);

  const [isGenerating, setIsGenerating] = useState(false);
  const [proposal, setProposal] = useState<any | null>(null);
  const [approvedIds, setApprovedIds] = useState<Set<string>>(new Set());
  const [questionBanks, setQuestionBanks] = useState<any[]>([]);
  const [selectedBankId, setSelectedBankId] = useState<string>('');
  const [isApproving, setIsApproving] = useState(false);
  const [approvalResult, setApprovalResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  // AI Pattern recommendation state
  const [recommendedPattern, setRecommendedPattern] = useState<any | null>(null);
  const [isRecommending, setIsRecommending] = useState(false);
  const [isLaunchingTemplate, setIsLaunchingTemplate] = useState(false);

  // Fetch AI template recommendation based on role & skills
  const fetchPatternRecommendation = async (title: string, sen: string, skillsStr: string) => {
    if (!title.trim()) return;
    setIsRecommending(true);
    try {
      const skillsArray = skillsStr.split(',').map((s) => s.trim()).filter(Boolean);
      const res = await apiRequest('/ai/copilot/recommend-template', {
        method: 'POST',
        body: JSON.stringify({
          role_title: title,
          seniority: sen,
          target_skills: skillsArray,
        }),
      });
      setRecommendedPattern(res);
      if (res.suggested_duration_minutes) {
        setDurationMinutes(res.suggested_duration_minutes);
      }
    } catch (err) {
      console.error('Failed to get template recommendation:', err);
    } finally {
      setIsRecommending(false);
    }
  };

  // Launch assessment directly from recommended pattern
  const handleLaunchRecommendedPattern = async () => {
    if (!recommendedPattern) return;
    setIsLaunchingTemplate(true);
    setError(null);
    try {
      const meta = TEMPLATE_META[recommendedPattern.recommended_template_key];
      const res = await apiRequest('/assessments/create-from-template', {
        method: 'POST',
        body: JSON.stringify({
          template_key: recommendedPattern.recommended_template_key,
          title: `${roleTitle} Assessment (${meta?.name || 'Standard'})`,
          duration_minutes: recommendedPattern.suggested_duration_minutes || durationMinutes,
        }),
      });
      navigate(`/assessments/${res.assessment_id}/build`);
    } catch (err: any) {
      setError(err.message || 'Failed to launch template assessment');
    } finally {
      setIsLaunchingTemplate(false);
    }
  };

  // Load question banks for destination selector and fetch recommended pattern
  useEffect(() => {
    const loadBanks = async () => {
      try {
        const banks = await apiRequest('/questions/banks');
        setQuestionBanks(banks);
        if (banks.length > 0) {
          setSelectedBankId(banks[0].id);
        }
      } catch (err) {
        console.error('Failed to load banks:', err);
      }
    };
    loadBanks();
    fetchPatternRecommendation(roleTitle, seniority, targetSkills);
  }, []);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    setProposal(null);
    setApprovalResult(null);

    const skillsArray = targetSkills.split(',').map((s) => s.trim()).filter(Boolean);

    try {
      const res = await apiRequest('/ai/copilot/propose', {
        method: 'POST',
        body: JSON.stringify({
          role_title: roleTitle,
          seniority,
          target_skills: skillsArray,
          duration_minutes: durationMinutes,
          include_coding: includeCoding,
          include_sql: includeSql,
          mcq_count: mcqCount,
        }),
      });
      setProposal(res);
      // Select all non-duplicate items by default for review
      const defaultApproved = new Set<string>();
      res.proposed_items.forEach((item: any) => {
        if (!item.duplicate_warning) {
          defaultApproved.add(item.item_id);
        }
      });
      setApprovedIds(defaultApproved);
    } catch (err: any) {
      setError(err.message || 'Failed to generate assessment proposal');
    } finally {
      setIsGenerating(false);
    }
  };

  const toggleItemApproval = (itemId: string) => {
    const next = new Set(approvedIds);
    if (next.has(itemId)) next.delete(itemId);
    else next.add(itemId);
    setApprovedIds(next);
  };

  const handleApproveAndPublish = async () => {
    if (!proposal || !selectedBankId || approvedIds.size === 0) return;
    setIsApproving(true);
    setError(null);

    try {
      const res = await apiRequest(`/ai/copilot/proposals/${proposal.proposal_id}/approve`, {
        method: 'POST',
        body: JSON.stringify({
          target_bank_id: selectedBankId,
          approved_item_ids: Array.from(approvedIds),
          notes: `Recruiter approved ${approvedIds.size} of ${proposal.total_items} items via Copilot Review Gate.`,
        }),
      });
      setApprovalResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to approve and publish items');
    } finally {
      setIsApproving(false);
    }
  };

  return (
    <div style={{ maxWidth: '1180px', margin: '2rem auto', padding: '0 1.5rem' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            width: '42px', height: '42px', borderRadius: '12px',
            background: 'linear-gradient(135deg, #6366F1, #EC4899)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 25px rgba(99, 102, 241, 0.4)',
          }}>
            <Bot size={24} color="#FFF" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.75rem', margin: 0 }}>Assessment Copilot</h1>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>
              AI-generated multi-modal assessment proposals with human-in-the-loop review gating
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span className="badge badge-secondary" style={{ fontSize: '0.75rem' }}>
            Human Approval Required
          </span>
        </div>
      </div>

      {/* Main Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '2rem', alignItems: 'start' }}>
        {/* Left Form: Copilot Controls */}
        <div className="card" style={{ padding: '1.75rem' }}>
          <h3 style={{ fontSize: '1.15rem', marginBottom: '1.2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sparkles size={18} color="var(--primary)" /> Role & Skill Parameters
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, margin: 0 }}>
                  Job Role / Position
                </label>
                <button
                  type="button"
                  onClick={() => fetchPatternRecommendation(roleTitle, seniority, targetSkills)}
                  disabled={isRecommending || !roleTitle.trim()}
                  style={{
                    background: 'none', border: 'none', color: 'var(--primary)',
                    fontSize: '0.72rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.25rem', padding: 0
                  }}
                >
                  <RefreshCw size={11} className={isRecommending ? 'spin' : ''} />
                  Analyze Pattern
                </button>
              </div>
              <input
                type="text"
                className="form-input"
                value={roleTitle}
                onChange={(e) => setRoleTitle(e.target.value)}
                onBlur={() => fetchPatternRecommendation(roleTitle, seniority, targetSkills)}
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '0.35rem' }}>
                Seniority Level
              </label>
              <select
                className="form-input"
                value={seniority}
                onChange={(e) => {
                  setSeniority(e.target.value);
                  fetchPatternRecommendation(roleTitle, e.target.value, targetSkills);
                }}
                style={{ width: '100%' }}
              >
                <option value="JUNIOR">Junior (0-2 yrs)</option>
                <option value="MID">Mid-Level (2-5 yrs)</option>
                <option value="SENIOR">Senior (5+ yrs)</option>
                <option value="LEAD">Tech Lead / Principal</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '0.35rem' }}>
                Target Skills (comma separated)
              </label>
              <textarea
                className="form-input"
                rows={2}
                value={targetSkills}
                onChange={(e) => setTargetSkills(e.target.value)}
                onBlur={() => fetchPatternRecommendation(roleTitle, seniority, targetSkills)}
                style={{ width: '100%' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '0.35rem' }}>
                  Duration (min)
                </label>
                <input
                  type="number"
                  className="form-input"
                  value={durationMinutes}
                  onChange={(e) => setDurationMinutes(Number(e.target.value))}
                  style={{ width: '100%' }}
                />
              </div>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '0.35rem' }}>
                  MCQ Count
                </label>
                <input
                  type="number"
                  className="form-input"
                  min={1}
                  max={10}
                  value={mcqCount}
                  onChange={(e) => setMcqCount(Number(e.target.value))}
                  style={{ width: '100%' }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', paddingTop: '0.5rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={includeCoding}
                  onChange={(e) => setIncludeCoding(e.target.checked)}
                />
                Include Algorithmic Coding Challenge
              </label>

              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={includeSql}
                  onChange={(e) => setIncludeSql(e.target.checked)}
                />
                Include SQL Aggregation Challenge
              </label>
            </div>

            {error && (
              <div className="alert alert-error" style={{ fontSize: '0.8rem' }}>
                {error}
              </div>
            )}

            <button
              onClick={handleGenerate}
              className="btn btn-primary"
              disabled={isGenerating || !roleTitle.trim()}
              style={{ marginTop: '0.5rem', padding: '0.85rem' }}
            >
              {isGenerating ? (
                <><Loader2 size={16} className="spin" /> Generating Proposal...</>
              ) : (
                <><Sparkles size={16} /> Synthesize Proposal</>
              )}
            </button>
          </div>
        </div>

        {/* Right Area: Proposal & Review Gate */}
        <div>
          {/* AI Pattern Recommendation Banner */}
          {recommendedPattern && (
            <div style={{
              marginBottom: '1.5rem',
              padding: '1.25rem 1.5rem',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.12), rgba(168, 85, 247, 0.08))',
              border: '1px solid rgba(99, 102, 241, 0.35)',
              boxShadow: '0 8px 30px rgba(0, 0, 0, 0.25)',
            }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start', flex: 1, minWidth: '280px' }}>
                  <div style={{
                    width: '48px', height: '48px', borderRadius: '12px',
                    background: 'rgba(99, 102, 241, 0.25)',
                    border: '1px solid rgba(99, 102, 241, 0.4)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '1.6rem', flexShrink: 0,
                  }}>
                    {TEMPLATE_META[recommendedPattern.recommended_template_key]?.icon || '🎯'}
                  </div>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.35rem' }}>
                      <span style={{
                        fontSize: '0.7rem', fontWeight: 800, textTransform: 'uppercase',
                        letterSpacing: '0.08em', padding: '0.2rem 0.6rem', borderRadius: '999px',
                        background: 'linear-gradient(135deg, #6366f1, #a855f7)', color: '#fff',
                        display: 'inline-flex', alignItems: 'center', gap: '0.3rem',
                      }}>
                        <Sparkles size={11} /> Copilot Recommended Pattern
                      </span>
                      <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#34d399' }}>
                        {Math.round(recommendedPattern.confidence * 100)}% Role Alignment
                      </span>
                    </div>

                    <h3 style={{ fontSize: '1.2rem', fontWeight: 700, margin: '0 0 0.35rem 0', color: '#fff' }}>
                      {TEMPLATE_META[recommendedPattern.recommended_template_key]?.name || recommendedPattern.recommended_template_key}
                    </h3>

                    <p style={{ fontSize: '0.85rem', color: 'rgba(255, 255, 255, 0.8)', margin: 0, lineHeight: 1.45 }}>
                      {recommendedPattern.rationale}
                    </p>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', marginTop: '0.75rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      <span>⏱️ Suggested Duration: <strong style={{ color: 'var(--text-main)' }}>{recommendedPattern.suggested_duration_minutes} mins</strong></span>
                      <span>🏢 Best For: <strong style={{ color: 'var(--text-main)' }}>{TEMPLATE_META[recommendedPattern.recommended_template_key]?.tag}</strong></span>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', alignSelf: 'center' }}>
                  <button
                    onClick={handleLaunchRecommendedPattern}
                    disabled={isLaunchingTemplate}
                    className="btn btn-primary"
                    style={{
                      whiteSpace: 'nowrap',
                      background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                      boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)',
                      padding: '0.7rem 1.3rem',
                      fontWeight: 700,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      cursor: 'pointer',
                    }}
                  >
                    {isLaunchingTemplate ? (
                      <><Loader2 size={16} className="spin" /> Deploying Pattern...</>
                    ) : (
                      <><Zap size={16} /> Instant Build with Pattern <ArrowRight size={15} /></>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}

          {!proposal && !approvalResult && (
            <div className="card" style={{ padding: '4rem 2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              <Bot size={48} style={{ opacity: 0.3, marginBottom: '1rem' }} />
              <h3>No Active Assessment Proposal</h3>
              <p style={{ maxWidth: '440px', margin: '0.5rem auto 0 auto', fontSize: '0.9rem' }}>
                Fill in the role requirements and click <strong>Synthesize Proposal</strong> to generate a balanced question mix, or click <strong>Instant Build with Pattern</strong> above to start with pre-structured sections!
              </p>
            </div>
          )}

          {/* Proposal Review Table */}
          {proposal && !approvalResult && (
            <div>
              {/* Approval Gate Banner */}
              <div style={{
                padding: '1rem 1.25rem',
                borderRadius: '10px',
                backgroundColor: 'rgba(99, 102, 241, 0.08)',
                border: '1px solid rgba(99, 102, 241, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '1.5rem',
              }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.95rem', color: '#c4b5fd' }}>
                    Proposal Draft • Status: {proposal.status}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {proposal.total_items} items proposed • {approvedIds.size} vetted for approval
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <select
                    className="form-input"
                    value={selectedBankId}
                    onChange={(e) => setSelectedBankId(e.target.value)}
                    style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}
                  >
                    {questionBanks.map((b) => (
                      <option key={b.id} value={b.id}>Bank: {b.name}</option>
                    ))}
                  </select>

                  <button
                    onClick={handleApproveAndPublish}
                    className="btn btn-primary btn-sm"
                    disabled={isApproving || approvedIds.size === 0}
                  >
                    {isApproving ? (
                      <><Loader2 size={14} className="spin" /> Approving...</>
                    ) : (
                      <><Check size={14} /> Approve ({approvedIds.size}) & Publish</>
                    )}
                  </button>
                </div>
              </div>

              {/* Proposed Items List */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {proposal.proposed_items.map((item: any) => {
                  const isApproved = approvedIds.has(item.item_id);
                  return (
                    <div
                      key={item.item_id}
                      style={{
                        padding: '1.25rem',
                        borderRadius: '10px',
                        backgroundColor: isApproved ? 'rgba(99, 102, 241, 0.05)' : 'rgba(255, 255, 255, 0.02)',
                        border: `1px solid ${isApproved ? 'var(--primary)' : 'var(--border-color)'}`,
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                          <span className="badge badge-primary" style={{ fontSize: '0.7rem' }}>{item.type}</span>
                          <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>{item.title}</span>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span className="badge badge-secondary" style={{ fontSize: '0.65rem' }}>{item.difficulty}</span>
                          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{item.points} pts</span>
                          <button
                            type="button"
                            onClick={() => toggleItemApproval(item.item_id)}
                            className={`btn btn-sm ${isApproved ? 'btn-primary' : 'btn-secondary'}`}
                            style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem' }}
                          >
                            {isApproved ? '✓ Approved' : 'Review / Approve'}
                          </button>
                        </div>
                      </div>

                      <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                        {item.content_markdown || item.description_markdown}
                      </p>

                      {/* Duplicate Warning Alert */}
                      {item.duplicate_warning && (
                        <div style={{
                          padding: '0.45rem 0.75rem',
                          borderRadius: '6px',
                          backgroundColor: 'rgba(245, 158, 11, 0.1)',
                          border: '1px solid rgba(245, 158, 11, 0.3)',
                          fontSize: '0.75rem',
                          color: '#fbbf24',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.4rem',
                          marginBottom: '0.75rem',
                        }}>
                          <AlertTriangle size={14} />
                          <span>{item.duplicate_warning}</span>
                        </div>
                      )}

                      {/* Options Preview for MCQs */}
                      {item.options && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                          {item.options.map((opt: any, oi: number) => (
                            <div key={oi} style={{
                              fontSize: '0.75rem',
                              padding: '0.25rem 0.5rem',
                              borderRadius: '4px',
                              backgroundColor: opt.is_correct ? 'rgba(16, 185, 129, 0.1)' : 'transparent',
                              color: opt.is_correct ? 'var(--success)' : 'var(--text-muted)',
                            }}>
                              {opt.is_correct ? '✓ ' : '• '}{opt.option_text}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Success Outcome */}
          {approvalResult && (
            <div className="card" style={{ padding: '3.5rem 2rem', textAlign: 'center' }}>
              <div style={{
                width: '60px', height: '60px', borderRadius: '50%',
                backgroundColor: 'rgba(16, 185, 129, 0.15)',
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                marginBottom: '1.2rem',
              }}>
                <CheckCircle2 size={36} color="var(--success)" />
              </div>
              <h2 style={{ fontSize: '1.5rem', marginBottom: '0.4rem' }}>
                Human Review Approved & Published!
              </h2>
              <p style={{ color: 'var(--text-muted)', maxWidth: '460px', margin: '0 auto 1.5rem auto', fontSize: '0.9rem' }}>
                Successfully vetted and saved <strong>{approvalResult.items_approved} questions</strong> into question bank <strong>{approvalResult.target_bank_name}</strong>.
              </p>
              <button
                onClick={() => { setProposal(null); setApprovalResult(null); }}
                className="btn btn-primary"
              >
                Synthesize Another Assessment
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
