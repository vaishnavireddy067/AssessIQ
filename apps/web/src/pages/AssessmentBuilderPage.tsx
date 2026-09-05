import React, { useEffect, useState, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { apiRequest } from '../api/client';
import { 
  ArrowLeft, Clock, Award, CheckCircle2, Plus, Trash2, 
  Layers, FileText, Check, AlertCircle, Sparkles, Bookmark,
  Lock, Save, Filter
} from 'lucide-react';

export const AssessmentBuilderPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [assessment, setAssessment] = useState<any | null>(null);
  const [banks, setBanks] = useState<any[]>([]);
  const [selectedBankId, setSelectedBankId] = useState<string>('');
  const [bankQuestions, setBankQuestions] = useState<any[]>([]);
  const [bankTypeFilter, setBankTypeFilter] = useState<string>('ALL');
  const [targetSection, setTargetSection] = useState<string>('');

  const [isLoading, setIsLoading] = useState(true);
  const [isPublishing, setIsPublishing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Save as Template Modal
  const [showSaveTemplateModal, setShowSaveTemplateModal] = useState(false);
  const [templateTitle, setTemplateTitle] = useState('');
  const [templateCategory, setTemplateCategory] = useState('CUSTOM');
  const [templateDescription, setTemplateDescription] = useState('');
  const [isSavingTemplate, setIsSavingTemplate] = useState(false);

  const loadAssessment = async () => {
    try {
      setIsLoading(true);
      const res = await apiRequest(`/assessments/${id}`);
      setAssessment(res);

      // Default target section
      if (res.sections_config?.sections && res.sections_config.sections.length > 0) {
        setTargetSection(res.sections_config.sections[0].name || 'General');
      } else {
        setTargetSection('General');
      }

      const banksRes = await apiRequest('/questions/banks');
      setBanks(banksRes);
      if (banksRes.length > 0 && !selectedBankId) {
        setSelectedBankId(banksRes[0].id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load assessment');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAssessment();
  }, [id]);

  useEffect(() => {
    const loadBankQuestions = async () => {
      if (!selectedBankId) return;
      try {
        const qRes = await apiRequest(`/questions/banks/${selectedBankId}/questions`);
        setBankQuestions(qRes);
      } catch (err) {
        console.error('Failed to load bank questions:', err);
      }
    };
    loadBankQuestions();
  }, [selectedBankId]);

  const handleAttachQuestion = async (qId: string) => {
    try {
      const updated = await apiRequest(`/assessments/${id}/questions`, {
        method: 'POST',
        body: JSON.stringify({
          question_ids: [qId],
          section_name: targetSection || 'General',
        }),
      });
      setAssessment(updated);
      setMessage(`Question linked to ${targetSection || 'General'}!`);
      setTimeout(() => setMessage(null), 2500);
    } catch (err: any) {
      setError(err.message || 'Failed to attach question');
    }
  };

  const handleDetachQuestion = async (qId: string) => {
    try {
      const updated = await apiRequest(`/assessments/${id}/questions/${qId}`, {
        method: 'DELETE',
      });
      setAssessment(updated);
    } catch (err: any) {
      setError(err.message || 'Failed to remove question');
    }
  };

  const handlePublish = async () => {
    setIsPublishing(true);
    setError(null);
    try {
      const updated = await apiRequest(`/assessments/${id}/publish`, {
        method: 'POST',
      });
      setAssessment(updated);
      setMessage('Assessment published! Candidates can now receive invitations.');
    } catch (err: any) {
      setError(err.message || 'Failed to publish assessment');
    } finally {
      setIsPublishing(false);
    }
  };

  const handleSaveAsTemplate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSavingTemplate(true);
    try {
      const sections = assessment?.sections_config?.sections || [
        { id: 'sec_1', name: 'General Section', type: 'MIXED', duration_minutes: assessment?.duration_minutes || 60, question_count: assessment?.questions?.length || 10 }
      ];

      await apiRequest('/assessments/templates', {
        method: 'POST',
        body: JSON.stringify({
          title: templateTitle || `${assessment.title} Pattern`,
          category: templateCategory,
          description: templateDescription || `Reusable template based on ${assessment.title}`,
          duration_minutes: assessment.duration_minutes,
          passing_score_percentage: assessment.passing_score_percentage,
          allow_section_switching: assessment.allow_section_switching,
          sections: sections,
          features: ['Company Custom Pattern', 'Saved from Assessment Builder'],
        }),
      });

      setShowSaveTemplateModal(false);
      setMessage('Assessment saved as reusable company template!');
      setTimeout(() => setMessage(null), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to save template');
    } finally {
      setIsSavingTemplate(false);
    }
  };

  // Group attached questions by section
  const groupedQuestions = useMemo(() => {
    if (!assessment?.questions) return {};
    const map: Record<string, any[]> = {};
    assessment.questions.forEach((q: any) => {
      const sec = q.section_name || 'General';
      if (!map[sec]) map[sec] = [];
      map[sec].push(q);
    });
    return map;
  }, [assessment]);

  // Filter bank questions by type
  const filteredBankQuestions = bankQuestions.filter((q) => {
    if (bankTypeFilter === 'ALL') return true;
    if (bankTypeFilter === 'CODING') return q.question_type === 'CODING' || q.title.toLowerCase().includes('code') || q.title.toLowerCase().includes('algo');
    if (bankTypeFilter === 'SQL') return q.title.toLowerCase().includes('sql') || q.title.toLowerCase().includes('query');
    if (bankTypeFilter === 'APTITUDE') return q.tags?.includes('APTITUDE') || q.title.toLowerCase().includes('math') || q.title.toLowerCase().includes('time') || q.title.toLowerCase().includes('work');
    if (bankTypeFilter === 'REASONING') return q.tags?.includes('REASONING') || q.title.toLowerCase().includes('logic') || q.title.toLowerCase().includes('puzzle');
    return true;
  });

  if (isLoading) {
    return (
      <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        Loading assessment builder...
      </div>
    );
  }

  const attachedQuestionIds = new Set(assessment?.questions.map((q: any) => q.question_id));
  const configuredSections = assessment?.sections_config?.sections || [];

  return (
    <div style={{ maxWidth: '1240px', margin: '2rem auto', padding: '0 1.5rem' }}>
      
      {/* Top Navigation Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <button onClick={() => navigate('/assessments')} className="btn btn-secondary btn-sm">
            <ArrowLeft size={16} /> Back
          </button>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <h1 style={{ fontSize: '1.6rem' }}>{assessment?.title}</h1>
              <span className={`badge ${
                assessment?.status === 'PUBLISHED' ? 'badge-success' : 'badge-warning'
              }`}>
                {assessment?.status}
              </span>
              <span className="badge badge-primary" style={{ fontSize: '0.7rem' }}>
                {assessment?.company_pattern || 'CUSTOM'}
              </span>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Configure test rules, sectional allocations, and attach verified bank questions
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <button
            onClick={() => {
              setTemplateTitle(`${assessment.title} Pattern`);
              setShowSaveTemplateModal(true);
            }}
            className="btn btn-secondary btn-sm"
            style={{ borderColor: 'rgba(99, 102, 241, 0.4)', color: '#c4b5fd' }}
          >
            <Bookmark size={15} /> Save as Reusable Template
          </button>

          {assessment?.status !== 'PUBLISHED' ? (
            <button
              onClick={handlePublish}
              className="btn btn-primary btn-sm"
              disabled={isPublishing || assessment?.questions.length === 0}
            >
              <CheckCircle2 size={16} /> {isPublishing ? 'Publishing...' : 'Publish Assessment'}
            </button>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--success)', fontWeight: 600, fontSize: '0.88rem' }}>
              <CheckCircle2 size={18} /> Ready for Candidates
            </div>
          )}
        </div>
      </div>

      {message && (
        <div className="alert alert-success" style={{ marginBottom: '1.2rem' }}>
          <Check size={16} /> <span>{message}</span>
        </div>
      )}

      {error && (
        <div className="alert alert-error" style={{ marginBottom: '1.2rem' }}>
          <AlertCircle size={16} /> <span>{error}</span>
        </div>
      )}

      {/* Overview Stats Bar */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1.1rem 1.6rem' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '1.5rem', fontSize: '0.9rem' }}>
          <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Duration: </span>
              <strong>{assessment?.duration_minutes} Minutes</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Passing Grade: </span>
              <strong>{assessment?.passing_score_percentage}%</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Total Questions: </span>
              <strong style={{ color: 'var(--secondary)' }}>{assessment?.total_questions} Questions</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Total Score: </span>
              <strong style={{ color: 'var(--primary)' }}>{assessment?.total_points} Points</strong>
            </div>
          </div>

          <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            {assessment?.allow_section_switching ? (
              <span>🔄 Free Section Navigation</span>
            ) : (
              <span style={{ color: '#f87171', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <Lock size={12} /> Sequential Section Lock
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.15fr 1fr', gap: '1.75rem', alignItems: 'start' }}>
        
        {/* Left Column: Sectioned Attached Questions */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.2rem' }}>
            <h3 style={{ fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Layers size={18} color="var(--primary)" /> Assessment Sections &amp; Questions ({assessment?.questions.length})
            </h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {assessment?.total_points} Total Points
            </span>
          </div>

          {assessment?.questions.length === 0 ? (
            <div style={{
              padding: '2.8rem 1rem',
              textAlign: 'center',
              backgroundColor: 'rgba(255, 255, 255, 0.01)',
              borderRadius: '8px',
              border: '1px dashed var(--border-color)',
            }}>
              <FileText size={38} color="var(--text-dim)" style={{ margin: '0 auto 0.75rem' }} />
              <div style={{ fontWeight: 600, fontSize: '0.95rem', marginBottom: '0.3rem' }}>
                No questions attached yet
              </div>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-dim)', maxWidth: '360px', margin: '0 auto' }}>
                Select a target section on the right panel to begin adding questions from your technical banks.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              {Object.entries(groupedQuestions).map(([secName, qList]) => (
                <div key={secName} style={{
                  borderRadius: '10px',
                  border: '1px solid var(--border-color)',
                  backgroundColor: 'rgba(255, 255, 255, 0.015)',
                  overflow: 'hidden',
                }}>
                  {/* Section Title Bar */}
                  <div style={{
                    padding: '0.65rem 1rem',
                    backgroundColor: 'rgba(255, 255, 255, 0.03)',
                    borderBottom: '1px solid var(--border-color)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '0.82rem',
                    fontWeight: 700,
                  }}>
                    <span style={{ color: '#c4b5fd', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <Layers size={14} /> {secName}
                    </span>
                    <span style={{ color: 'var(--text-dim)', fontWeight: 500 }}>
                      {qList.length} Questions
                    </span>
                  </div>

                  {/* Section Question Items */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', padding: '0.85rem' }}>
                    {qList.map((q: any, idx: number) => (
                      <div
                        key={q.id}
                        style={{
                          padding: '0.85rem',
                          borderRadius: '6px',
                          backgroundColor: 'rgba(255, 255, 255, 0.02)',
                          border: '1px solid var(--border-color)',
                          display: 'flex',
                          alignItems: 'flex-start',
                          justifyContent: 'space-between',
                          gap: '0.85rem',
                        }}
                      >
                        <div style={{ flex: 1 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.25rem' }}>
                            <span className="badge badge-primary" style={{ fontSize: '0.62rem' }}>
                              #{idx + 1}
                            </span>
                            <span className="badge badge-secondary" style={{ fontSize: '0.62rem' }}>
                              {q.difficulty}
                            </span>
                            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                              {q.points} pts
                            </span>
                          </div>
                          <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.2rem' }}>
                            {q.title}
                          </div>
                          <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)', maxHeight: '36px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {q.content_markdown}
                          </div>
                        </div>

                        <button
                          onClick={() => handleDetachQuestion(q.question_id)}
                          className="btn btn-secondary btn-sm"
                          style={{ color: 'var(--danger)', borderColor: 'rgba(239, 68, 68, 0.2)', padding: '0.35rem 0.5rem' }}
                          title="Remove from section"
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Question Bank Browser & Section Targeting */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.2rem' }}>
            <h3 style={{ fontSize: '1.2rem' }}>Question Bank Explorer</h3>
            <Link to="/questions" className="btn btn-secondary btn-sm" style={{ fontSize: '0.75rem' }}>
              + Manage Banks
            </Link>
          </div>

          {/* Target Section Selector */}
          <div className="form-group" style={{ marginBottom: '1rem' }}>
            <label className="form-label" style={{ fontSize: '0.8rem', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <Layers size={13} color="var(--primary)" /> Target Assessment Section (Attach To)
            </label>
            <select
              className="form-select"
              value={targetSection}
              onChange={(e) => setTargetSection(e.target.value)}
            >
              {configuredSections.length > 0 ? (
                configuredSections.map((s: any) => (
                  <option key={s.id || s.name} value={s.name}>
                    {s.name} ({s.duration_minutes || 20}m)
                  </option>
                ))
              ) : (
                <>
                  <option value="General">General Section</option>
                  <option value="Part A: Aptitude & Reasoning">Part A: Aptitude &amp; Reasoning</option>
                  <option value="Part B: Technical & Coding">Part B: Technical &amp; Coding</option>
                </>
              )}
            </select>
          </div>

          {/* Question Bank Select */}
          <div className="form-group" style={{ marginBottom: '1rem' }}>
            <label className="form-label" style={{ fontSize: '0.8rem' }}>Source Question Bank</label>
            <select
              className="form-select"
              value={selectedBankId}
              onChange={(e) => setSelectedBankId(e.target.value)}
            >
              {banks.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name} ({b.questions_count} questions)
                </option>
              ))}
            </select>
          </div>

          {/* Quick Domain Filter Chips */}
          <div style={{ display: 'flex', gap: '0.35rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
            {[
              { id: 'ALL', label: 'All' },
              { id: 'APTITUDE', label: 'Aptitude' },
              { id: 'REASONING', label: 'Reasoning' },
              { id: 'CODING', label: 'Coding' },
              { id: 'SQL', label: 'SQL' },
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setBankTypeFilter(f.id)}
                style={{
                  padding: '0.2rem 0.6rem',
                  borderRadius: '4px',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  border: `1px solid ${bankTypeFilter === f.id ? 'var(--primary)' : 'var(--border-color)'}`,
                  backgroundColor: bankTypeFilter === f.id ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.02)',
                  color: bankTypeFilter === f.id ? '#FFF' : 'var(--text-muted)',
                }}
              >
                {f.label}
              </button>
            ))}
          </div>

          {/* Bank Question Items List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', maxHeight: '480px', overflowY: 'auto' }}>
            {filteredBankQuestions.length === 0 ? (
              <p style={{ fontSize: '0.85rem', color: 'var(--text-dim)', textAlign: 'center', padding: '1.5rem' }}>
                No matching questions in this bank.
              </p>
            ) : (
              filteredBankQuestions.map((q) => {
                const isAttached = attachedQuestionIds.has(q.id);
                return (
                  <div
                    key={q.id}
                    style={{
                      padding: '0.8rem 0.95rem',
                      borderRadius: '8px',
                      backgroundColor: isAttached ? 'rgba(99, 102, 241, 0.06)' : 'rgba(255, 255, 255, 0.02)',
                      border: `1px solid ${isAttached ? 'rgba(99, 102, 241, 0.3)' : 'var(--border-color)'}`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: '0.75rem',
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{q.title}</div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        {q.difficulty} • {q.points} pts • {q.options?.length || 0} choices
                      </div>
                    </div>

                    {isAttached ? (
                      <span className="badge badge-success" style={{ fontSize: '0.62rem' }}>
                        <Check size={11} /> Linked
                      </span>
                    ) : (
                      <button
                        onClick={() => handleAttachQuestion(q.id)}
                        className="btn btn-secondary btn-sm"
                        style={{ fontSize: '0.75rem', padding: '0.35rem 0.7rem' }}
                      >
                        <Plus size={13} /> Link
                      </button>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* ── Save as Custom Template Modal ────────────────────────────────────── */}
      {showSaveTemplateModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(6px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 200, padding: '1rem',
        }}>
          <div className="card" style={{ maxWidth: '480px', width: '100%', padding: '2rem' }}>
            <h3 style={{ marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Bookmark size={20} color="var(--primary)" /> Save as Reusable Template
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.2rem' }}>
              Store this assessment layout in your company's library to instantly reuse for future recruitment drives.
            </p>

            <form onSubmit={handleSaveAsTemplate}>
              <div className="form-group">
                <label className="form-label">Template Title *</label>
                <input
                  type="text"
                  className="form-input"
                  value={templateTitle}
                  onChange={(e) => setTemplateTitle(e.target.value)}
                  placeholder="e.g. Acme SDE-1 Assessment Pattern"
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Category</label>
                <select
                  className="form-select"
                  value={templateCategory}
                  onChange={(e) => setTemplateCategory(e.target.value)}
                >
                  <option value="CODING_ONLY">Coding-Only (DSA)</option>
                  <option value="TECHNICAL_MCQ">Technical Fundamentals + MCQ</option>
                  <option value="APTITUDE_REASONING">Aptitude &amp; Reasoning</option>
                  <option value="VERBAL_APTITUDE">Verbal &amp; Communication</option>
                  <option value="FULL_CAMPUS">Full Campus Recruitment Pattern</option>
                  <option value="CUSTOM">Custom Company Pattern</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Description (Optional)</label>
                <textarea
                  className="form-input"
                  rows={3}
                  value={templateDescription}
                  onChange={(e) => setTemplateDescription(e.target.value)}
                  placeholder="Explain who this assessment pattern is intended for..."
                />
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ flex: 1 }}
                  onClick={() => setShowSaveTemplateModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ flex: 2, fontWeight: 700 }}
                  disabled={isSavingTemplate}
                >
                  {isSavingTemplate ? 'Saving...' : 'Save into Company Library'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
