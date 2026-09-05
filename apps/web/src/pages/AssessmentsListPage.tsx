import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { apiRequest } from '../api/client';
import {
  FileText, Plus, Clock, Award, Users, CheckCircle2,
  ExternalLink, Copy, Check, ChevronRight, Play, Sparkles,
  Building2, Zap, ChevronDown, Calendar, AlertCircle, Layers,
  Lock, ArrowRight, Code2, Puzzle, Brain, MessageSquare, GraduationCap, Edit3, Trash2
} from 'lucide-react';
import { ResumeAnalysisModal } from '../components/ResumeAnalysisModal';

// ── Pattern / Company Theme Metadata ──────────────────────────────────────────
const PATTERN_META: Record<string, { emoji: string; color: string; gradient: string; label: string }> = {
  CODING_ONLY:        { emoji: '🖥️', color: '#3b82f6', gradient: 'linear-gradient(135deg,rgba(59,130,246,0.2),rgba(59,130,246,0.05))', label: 'Coding-Only (DSA)' },
  TECHNICAL_MCQ:      { emoji: '🧩', color: '#8b5cf6', gradient: 'linear-gradient(135deg,rgba(139,92,246,0.2),rgba(139,92,246,0.05))', label: 'Tech Fundamentals + MCQ' },
  APTITUDE_REASONING: { emoji: '🧠', color: '#10b981', gradient: 'linear-gradient(135deg,rgba(16,185,129,0.2),rgba(16,185,129,0.05))', label: 'Aptitude + Reasoning' },
  VERBAL_APTITUDE:    { emoji: '🗣️', color: '#ec4899', gradient: 'linear-gradient(135deg,rgba(236,72,153,0.2),rgba(236,72,153,0.05))', label: 'Verbal + Aptitude' },
  FULL_CAMPUS:        { emoji: '🎓', color: '#f59e0b', gradient: 'linear-gradient(135deg,rgba(245,158,11,0.2),rgba(245,158,11,0.05))', label: 'Full Campus Pattern' },
  TCS_ION:            { emoji: '🔵', color: '#1a56db', gradient: 'linear-gradient(135deg,#1a56db22,#1a56db08)', label: 'TCS iON' },
  INFOSYS_INFYTQ:     { emoji: '🟣', color: '#7c3aed', gradient: 'linear-gradient(135deg,#7c3aed22,#7c3aed08)', label: 'Infosys InfyTQ' },
  WIPRO_AMCAT:        { emoji: '🟢', color: '#059669', gradient: 'linear-gradient(135deg,#05966922,#05966908)', label: 'Wipro AMCAT' },
  ACCENTURE_COGNITIVE:{ emoji: '🟠', color: '#d97706', gradient: 'linear-gradient(135deg,#d9770622,#d9770608)', label: 'Accenture' },
  CUSTOM:             { emoji: '✏️', color: '#6366f1', gradient: 'linear-gradient(135deg,rgba(99,102,241,0.2),rgba(99,102,241,0.05))', label: 'Custom' },
};

export const AssessmentsListPage: React.FC = () => {
  const navigate = useNavigate();
  const [assessments, setAssessments] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showResumeModal, setShowResumeModal] = useState(false);

  // ── Create from scratch modal ────────────────────────────────────────────────
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [title, setTitle] = useState('');
  const [slug, setSlug] = useState('');
  const [duration, setDuration] = useState(30);
  const [passingScore, setPassingScore] = useState(60);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ── Pattern Templates Gallery modal ──────────────────────────────────────────
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [templates, setTemplates] = useState<any[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<any | null>(null);
  const [templateCategoryFilter, setTemplateCategoryFilter] = useState('ALL');
  const [templateCustomTitle, setTemplateCustomTitle] = useState('');
  const [templateCustomDuration, setTemplateCustomDuration] = useState(60);
  const [templateCustomPassingScore, setTemplateCustomPassingScore] = useState(65);
  const [templateValidityHours, setTemplateValidityHours] = useState(72);
  const [templateAllowSwitching, setTemplateAllowSwitching] = useState(true);
  const [isCreatingFromTemplate, setIsCreatingFromTemplate] = useState(false);
  const [templateError, setTemplateError] = useState<string | null>(null);

  // ── Company Blueprint modal (Legacy/Specific) ────────────────────────────────
  const [showBlueprintModal, setShowBlueprintModal] = useState(false);
  const [blueprints, setBlueprints] = useState<any[]>([]);
  const [selectedBlueprint, setSelectedBlueprint] = useState<any | null>(null);
  const [blueprintTitle, setBlueprintTitle] = useState('');
  const [blueprintValidityHours, setBlueprintValidityHours] = useState(72);
  const [isCreatingBlueprint, setIsCreatingBlueprint] = useState(false);
  const [blueprintError, setBlueprintError] = useState<string | null>(null);

  // ── Invite modal ─────────────────────────────────────────────────────────────
  const [inviteModalAss, setInviteModalAss] = useState<any | null>(null);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteName, setInviteName] = useState('');
  const [generatedLink, setGeneratedLink] = useState<string | null>(null);
  const [isInviting, setIsInviting] = useState(false);
  const [copied, setCopied] = useState(false);

  const loadAssessments = async () => {
    try {
      setIsLoading(true);
      const res = await apiRequest('/assessments');
      setAssessments(res);
    } catch (err) {
      console.error('Failed to load assessments:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAssessments();
  }, []);

  // ── Auto-slug helper ──────────────────────────────────────────────────────────
  const handleTitleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setTitle(val);
    setSlug(val.toLowerCase().replace(/[^a-z0-9]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, ''));
  };

  // ── Open Pattern Templates Modal ──────────────────────────────────────────────
  const openTemplateModal = async (categoryFilter = 'ALL') => {
    setShowTemplateModal(true);
    setTemplateError(null);
    setTemplateCategoryFilter(categoryFilter);
    try {
      const data = await apiRequest('/assessments/templates');
      setTemplates(data);
      if (data.length > 0) {
        handleSelectTemplate(data[0]);
      }
    } catch (err: any) {
      setTemplateError(err.message || 'Failed to load pattern templates');
    }
  };

  const handleSelectTemplate = (tmpl: any) => {
    setSelectedTemplate(tmpl);
    setTemplateCustomTitle(tmpl.title);
    setTemplateCustomDuration(tmpl.duration_minutes || 60);
    setTemplateCustomPassingScore(tmpl.passing_score_percentage || 60);
    setTemplateAllowSwitching(tmpl.allow_section_switching !== undefined ? tmpl.allow_section_switching : true);
    setTemplateError(null);
  };

  // ── Instantiate Assessment from Template ──────────────────────────────────────
  const handleCreateFromTemplate = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!selectedTemplate) return;
    setTemplateError(null);
    setIsCreatingFromTemplate(true);
    try {
      const payload: any = {
        title: templateCustomTitle || selectedTemplate.title,
        duration_minutes: Number(templateCustomDuration),
        passing_score_percentage: Number(templateCustomPassingScore),
        allow_section_switching: templateAllowSwitching,
        validity_hours: templateValidityHours,
      };

      if (selectedTemplate.is_company_custom && selectedTemplate.id) {
        payload.template_id = selectedTemplate.id;
      } else {
        payload.template_key = selectedTemplate.key;
      }

      const created = await apiRequest('/assessments/create-from-template', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      setShowTemplateModal(false);
      await loadAssessments();
      navigate(`/assessments/${created.id}`);
    } catch (err: any) {
      setTemplateError(err.message || 'Failed to create assessment from template');
    } finally {
      setIsCreatingFromTemplate(false);
    }
  };

  // ── Create custom assessment ──────────────────────────────────────────────────
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsCreating(true);
    try {
      const created = await apiRequest('/assessments', {
        method: 'POST',
        body: JSON.stringify({ title, slug, duration_minutes: Number(duration), passing_score_percentage: Number(passingScore) }),
      });
      setShowCreateModal(false);
      navigate(`/assessments/${created.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to create assessment');
    } finally {
      setIsCreating(false);
    }
  };

  // ── Open legacy blueprint modal ───────────────────────────────────────────────
  const openBlueprintModal = async () => {
    setShowBlueprintModal(true);
    setBlueprintError(null);
    if (blueprints.length === 0) {
      try {
        const data = await apiRequest('/assessments/blueprints');
        setBlueprints(data);
        if (data.length > 0) {
          setSelectedBlueprint(data[0]);
          setBlueprintTitle(data[0].title);
        }
      } catch (err: any) {
        setBlueprintError(err.message || 'Failed to load blueprints');
      }
    }
  };

  const handleSelectBlueprint = (bp: any) => {
    setSelectedBlueprint(bp);
    setBlueprintTitle(bp.title);
    setBlueprintError(null);
  };

  const handleCreateFromBlueprint = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedBlueprint) return;
    setBlueprintError(null);
    setIsCreatingBlueprint(true);
    try {
      const created = await apiRequest('/assessments/create-from-blueprint', {
        method: 'POST',
        body: JSON.stringify({
          blueprint_key: selectedBlueprint.key,
          title: blueprintTitle || selectedBlueprint.title,
          validity_hours: blueprintValidityHours,
        }),
      });
      setShowBlueprintModal(false);
      await loadAssessments();
      navigate(`/assessments/${created.id}`);
    } catch (err: any) {
      setBlueprintError(err.message || 'Failed to create assessment from blueprint');
    } finally {
      setIsCreatingBlueprint(false);
    }
  };

  // ── Invite candidate ──────────────────────────────────────────────────────────
  const handleGenerateInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteModalAss) return;
    setIsInviting(true);
    try {
      const res = await apiRequest(`/assessments/${inviteModalAss.id}/invitations`, {
        method: 'POST',
        body: JSON.stringify({ candidate_email: inviteEmail, candidate_name: inviteName || undefined }),
      });
      setGeneratedLink(`${window.location.origin}/exam/${res.token}`);
    } catch (err: any) {
      alert(err.message || 'Failed to generate invitation');
    } finally {
      setIsInviting(false);
    }
  };

  const copyToClipboard = () => {
    if (generatedLink) {
      navigator.clipboard.writeText(generatedLink);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // ── Helper: pattern badge ─────────────────────────────────────────────────────
  const PatternBadge: React.FC<{ pattern: string }> = ({ pattern }) => {
    if (!pattern) return null;
    const meta = PATTERN_META[pattern] || PATTERN_META.CUSTOM;
    return (
      <span style={{
        fontSize: '0.72rem', fontWeight: 700, padding: '0.2rem 0.6rem',
        borderRadius: '9999px', background: meta.gradient,
        color: meta.color, border: `1px solid ${meta.color}44`,
        display: 'inline-flex', alignItems: 'center', gap: '0.35rem',
      }}>
        <span>{meta.emoji}</span>
        <span>{meta.label}</span>
      </span>
    );
  };

  // Filter templates by selected category
  const filteredTemplates = templates.filter((t) => {
    if (templateCategoryFilter === 'ALL') return true;
    if (templateCategoryFilter === 'COMPANY_SAVED') return t.is_company_custom;
    return t.category === templateCategoryFilter;
  });

  return (
    <div style={{ maxWidth: '1240px', margin: '2rem auto', padding: '0 1.5rem' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.85rem', marginBottom: '0.35rem' }}>Assessments &amp; Hiring Drives</h1>
          <p style={{ fontSize: '0.95rem', color: 'var(--text-muted)' }}>
            Choose ready-made pattern templates (Coding-Only, Campus, Aptitude) or build custom tests
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button
            onClick={() => setShowResumeModal(true)}
            className="btn btn-secondary"
            style={{ borderColor: '#8B5CF6', color: '#c4b5fd' }}
          >
            <Sparkles size={16} color="#8B5CF6" /> AI Resume Intelligence
          </button>
          
          <button
            onClick={() => openTemplateModal('ALL')}
            className="btn btn-primary"
            style={{
              background: 'linear-gradient(135deg, #6366F1 0%, #06B6D4 100%)',
              border: 'none',
              boxShadow: '0 4px 15px rgba(99, 102, 241, 0.35)',
              fontWeight: 700,
            }}
          >
            <Layers size={18} /> Choose Pattern Template
          </button>

          <button
            onClick={openBlueprintModal}
            className="btn btn-secondary"
            style={{ borderColor: 'rgba(6,182,212,0.4)', color: 'var(--secondary)' }}
          >
            <Building2 size={16} /> Company Blueprint
          </button>

          <button onClick={() => setShowCreateModal(true)} className="btn btn-secondary">
            <Plus size={16} /> Custom Scratch
          </button>
        </div>
      </div>

      {isLoading ? (
        <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading assessments...
        </div>
      ) : assessments.length === 0 ? (
        <div className="card" style={{ padding: '3.5rem', textAlign: 'center', border: '1px dashed var(--border-color)' }}>
          <FileText size={48} color="var(--primary)" style={{ margin: '0 auto 1rem', opacity: 0.8 }} />
          <h3 style={{ fontSize: '1.3rem', marginBottom: '0.5rem' }}>No assessments created yet</h3>
          <p style={{ maxWidth: '480px', margin: '0 auto 1.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            Start with our proven hiring pattern templates (Coding-Only, Tech+MCQ, Campus Drive) or design a custom test.
          </p>
          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button onClick={() => openTemplateModal('ALL')} className="btn btn-primary">
              <Layers size={16} /> Choose Pattern Template
            </button>
            <button onClick={openBlueprintModal} className="btn btn-secondary">
              <Building2 size={16} /> Company Blueprint
            </button>
          </div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '1.5rem' }}>
          {assessments.map((ass) => (
            <div key={ass.id} className="card card-hover" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.7rem', flexWrap: 'wrap', gap: '0.4rem' }}>
                  <span className={`badge ${
                    ass.status === 'PUBLISHED' ? 'badge-success' :
                    ass.status === 'DRAFT' ? 'badge-warning' : 'badge-primary'
                  }`}>
                    {ass.status}
                  </span>
                  <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                    <PatternBadge pattern={ass.company_pattern} />
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                      {ass.slug}
                    </span>
                  </div>
                </div>

                <h3 style={{ fontSize: '1.15rem', marginBottom: '0.5rem' }}>{ass.title}</h3>
                <p style={{
                  fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.2rem',
                  display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden'
                }}>
                  {ass.description || 'Proctored candidate evaluation on the AssessIQ Cloud Examination Sandbox.'}
                </p>

                {/* Section Structure Pill List */}
                {ass.sections_config?.sections && ass.sections_config.sections.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', marginBottom: '1.2rem' }}>
                    {ass.sections_config.sections.map((sec: any, idx: number) => (
                      <span key={idx} style={{
                        fontSize: '0.7rem', padding: '0.15rem 0.5rem', borderRadius: '4px',
                        backgroundColor: 'rgba(255, 255, 255, 0.04)', border: '1px solid var(--border-color)',
                        color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem',
                      }}>
                        <Layers size={10} color="var(--primary)" /> {sec.name || sec}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <div style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  paddingTop: '0.8rem', borderTop: '1px solid var(--border-color)',
                  fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '1rem',
                }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                    <Clock size={14} /> {ass.duration_minutes}m
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                    <Award size={14} /> Pass: {ass.passing_score_percentage}%
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                    <FileText size={14} /> {ass.total_questions || 0} Qs
                  </span>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <Link to={`/assessments/${ass.id}`} className="btn btn-secondary btn-sm" style={{ flex: 1 }}>
                    Configure &amp; Questions
                  </Link>
                  {ass.status === 'PUBLISHED' && (
                    <>
                      <button
                        onClick={() => { setInviteModalAss(ass); setGeneratedLink(null); setInviteEmail(''); setInviteName(''); }}
                        className="btn btn-primary btn-sm"
                        style={{ flex: 1 }}
                      >
                        Invite Candidate
                      </button>
                      <Link to={`/assessments/${ass.id}/results`} className="btn btn-secondary btn-sm">
                        <Users size={15} /> Results
                      </Link>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Pattern Templates Gallery Modal ─────────────────────────────────────── */}
      {showTemplateModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.82)', backdropFilter: 'blur(10px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 200, padding: '1rem',
        }}>
          <div className="card" style={{ maxWidth: '960px', width: '100%', padding: '2rem', maxHeight: '92vh', overflowY: 'auto' }}>
            
            {/* Modal Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.2rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                <div style={{
                  width: '44px', height: '44px', borderRadius: '12px',
                  background: 'linear-gradient(135deg, #6366F1, #06B6D4)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#FFF',
                }}>
                  <Layers size={24} />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.4rem', margin: 0 }}>Assessment Pattern Templates</h3>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>
                    Pick a ready-made hiring pattern tailored for your role, or reuse saved company templates
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowTemplateModal(false)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: '1.2rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            {templateError && (
              <div className="alert alert-error" style={{ marginBottom: '1.2rem' }}>
                <AlertCircle size={16} /> <span>{templateError}</span>
              </div>
            )}

            {/* Category Filter Tabs */}
            <div style={{ display: 'flex', gap: '0.4rem', overflowX: 'auto', paddingBottom: '0.5rem', marginBottom: '1.5rem' }}>
              {[
                { id: 'ALL', label: 'All Patterns', emoji: '🌟' },
                { id: 'CODING_ONLY', label: 'Coding-Only (DSA)', emoji: '🖥️' },
                { id: 'TECHNICAL_MCQ', label: 'Technical + MCQ', emoji: '🧩' },
                { id: 'APTITUDE_REASONING', label: 'Aptitude & Reasoning', emoji: '🧠' },
                { id: 'VERBAL_APTITUDE', label: 'Verbal + Aptitude', emoji: '🗣️' },
                { id: 'FULL_CAMPUS', label: 'Campus Hiring Drives', emoji: '🎓' },
                { id: 'COMPANY_SAVED', label: 'Company Saved Library', emoji: '🏢' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setTemplateCategoryFilter(tab.id)}
                  style={{
                    padding: '0.45rem 0.85rem',
                    borderRadius: '8px',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    whiteSpace: 'nowrap',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.4rem',
                    border: `1px solid ${templateCategoryFilter === tab.id ? 'var(--primary)' : 'var(--border-color)'}`,
                    backgroundColor: templateCategoryFilter === tab.id ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.02)',
                    color: templateCategoryFilter === tab.id ? '#FFF' : 'var(--text-muted)',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <span>{tab.emoji}</span>
                  <span>{tab.label}</span>
                </button>
              ))}
            </div>

            {/* Template Cards Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
              {filteredTemplates.map((tmpl) => {
                const isSelected = selectedTemplate?.key === tmpl.key || (selectedTemplate?.id && selectedTemplate?.id === tmpl.id);
                return (
                  <div
                    key={tmpl.id || tmpl.key}
                    onClick={() => handleSelectTemplate(tmpl)}
                    style={{
                      padding: '1.2rem',
                      borderRadius: '12px',
                      cursor: 'pointer',
                      border: `2px solid ${isSelected ? tmpl.color : 'var(--border-color)'}`,
                      backgroundColor: isSelected ? `${tmpl.color}15` : 'rgba(255, 255, 255, 0.02)',
                      transition: 'all 0.2s ease',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
                        <span style={{ fontSize: '1.6rem' }}>{tmpl.emoji || '📋'}</span>
                        <div style={{ display: 'flex', gap: '0.3rem', alignItems: 'center' }}>
                          {tmpl.is_popular && (
                            <span style={{
                              fontSize: '0.68rem', fontWeight: 800, padding: '0.15rem 0.45rem',
                              borderRadius: '4px', backgroundColor: 'rgba(245, 158, 11, 0.2)', color: '#fbbf24',
                            }}>
                              🔥 Popular
                            </span>
                          )}
                          {tmpl.is_company_custom && (
                            <span style={{
                              fontSize: '0.68rem', fontWeight: 800, padding: '0.15rem 0.45rem',
                              borderRadius: '4px', backgroundColor: 'rgba(99, 102, 241, 0.2)', color: '#818cf8',
                            }}>
                              🏢 Company
                            </span>
                          )}
                        </div>
                      </div>

                      <h4 style={{ fontSize: '1.02rem', marginBottom: '0.4rem', color: isSelected ? tmpl.color : 'var(--text-main)' }}>
                        {tmpl.title}
                      </h4>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.4', marginBottom: '0.9rem' }}>
                        {tmpl.description}
                      </p>

                      {/* Sections Pills */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', marginBottom: '0.9rem' }}>
                        {tmpl.sections?.map((sec: any, i: number) => (
                          <div key={sec.id || i} style={{
                            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                            fontSize: '0.72rem', padding: '0.3rem 0.5rem', borderRadius: '6px',
                            backgroundColor: 'rgba(255, 255, 255, 0.03)', border: '1px solid var(--border-color)',
                          }}>
                            <span style={{ fontWeight: 600, color: 'var(--text-main)', maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {sec.name}
                            </span>
                            <span style={{ color: 'var(--text-dim)' }}>
                              {sec.duration_minutes}m
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      paddingTop: '0.6rem', borderTop: '1px solid var(--border-color)',
                      fontSize: '0.75rem', color: 'var(--text-dim)',
                    }}>
                      <span>{tmpl.duration_minutes}m total</span>
                      <span>{tmpl.allow_section_switching ? '🔄 Flexible' : '🔒 Sequential Lock'}</span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Customization & Launch Drawer */}
            {selectedTemplate && (
              <div style={{
                borderRadius: '12px',
                border: `1px solid ${selectedTemplate.color}44`,
                backgroundColor: 'rgba(255, 255, 255, 0.02)',
                padding: '1.5rem',
                marginBottom: '1rem',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                  <span style={{ fontSize: '1.3rem' }}>{selectedTemplate.emoji}</span>
                  <div style={{ fontWeight: 700, fontSize: '1.05rem', color: selectedTemplate.color }}>
                    Customize &amp; Launch: {selectedTemplate.title}
                  </div>
                </div>

                <form onSubmit={handleCreateFromTemplate}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr 1fr 1fr', gap: '0.85rem', marginBottom: '1.2rem' }}>
                    <div className="form-group" style={{ margin: 0 }}>
                      <label className="form-label" style={{ fontSize: '0.8rem' }}>Assessment Title *</label>
                      <input
                        type="text"
                        className="form-input"
                        value={templateCustomTitle}
                        onChange={(e) => setTemplateCustomTitle(e.target.value)}
                        required
                      />
                    </div>

                    <div className="form-group" style={{ margin: 0 }}>
                      <label className="form-label" style={{ fontSize: '0.8rem' }}>Duration (Mins)</label>
                      <input
                        type="number"
                        className="form-input"
                        value={templateCustomDuration}
                        onChange={(e) => setTemplateCustomDuration(Number(e.target.value))}
                        min={5} max={300}
                        required
                      />
                    </div>

                    <div className="form-group" style={{ margin: 0 }}>
                      <label className="form-label" style={{ fontSize: '0.8rem' }}>Pass Score (%)</label>
                      <input
                        type="number"
                        className="form-input"
                        value={templateCustomPassingScore}
                        onChange={(e) => setTemplateCustomPassingScore(Number(e.target.value))}
                        min={0} max={100}
                        required
                      />
                    </div>

                    <div className="form-group" style={{ margin: 0 }}>
                      <label className="form-label" style={{ fontSize: '0.8rem' }}>Drive Window</label>
                      <select
                        className="form-select"
                        value={templateValidityHours}
                        onChange={(e) => setTemplateValidityHours(Number(e.target.value))}
                      >
                        <option value={24}>24 hours</option>
                        <option value={48}>48 hours</option>
                        <option value={72}>3 days</option>
                        <option value={168}>7 days</option>
                        <option value={720}>30 days</option>
                      </select>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.2rem' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.82rem', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={templateAllowSwitching}
                        onChange={(e) => setTemplateAllowSwitching(e.target.checked)}
                      />
                      <span>Allow candidates to freely switch between sections (uncheck to enforce Sequential Section Lock)</span>
                    </label>

                    <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                      Auto-links relevant questions from your question bank
                    </span>
                  </div>

                  <div style={{ display: 'flex', gap: '0.85rem' }}>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      style={{ flex: 1 }}
                      onClick={() => setShowTemplateModal(false)}
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="btn btn-primary"
                      style={{
                        flex: 2,
                        background: `linear-gradient(135deg, ${selectedTemplate.color} 0%, #06B6D4 100%)`,
                        border: 'none',
                        fontWeight: 700,
                      }}
                      disabled={isCreatingFromTemplate}
                    >
                      {isCreatingFromTemplate ? 'Instantiating Assessment...' : `🚀 Deploy Assessment from Pattern`}
                    </button>
                  </div>
                </form>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Legacy Company Blueprint Modal ─────────────────────────────────────── */}
      {showBlueprintModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(8px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 200, padding: '1rem',
        }}>
          <div className="card" style={{ maxWidth: '780px', width: '100%', padding: '2rem', maxHeight: '90vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
              <div style={{
                width: '40px', height: '40px', borderRadius: '10px',
                background: 'linear-gradient(135deg,#06B6D4,#6366F1)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff',
              }}>
                <Building2 size={22} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.3rem', margin: 0 }}>Company Pattern Blueprints</h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', margin: 0 }}>
                  Pre-configured test patterns matching TCS, Infosys, Wipro &amp; Accenture drives
                </p>
              </div>
            </div>

            {blueprintError && (
              <div className="alert alert-error" style={{ margin: '1rem 0' }}>
                <AlertCircle size={16} /> <span>{blueprintError}</span>
              </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: '0.75rem', margin: '1.25rem 0' }}>
              {blueprints.map((bp) => {
                const meta = PATTERN_META[bp.key] || PATTERN_META.CUSTOM;
                const isSelected = selectedBlueprint?.key === bp.key;
                return (
                  <button
                    key={bp.key}
                    type="button"
                    onClick={() => handleSelectBlueprint(bp)}
                    style={{
                      padding: '1rem 0.75rem',
                      borderRadius: '12px',
                      border: `2px solid ${isSelected ? meta.color : 'var(--border-color)'}`,
                      background: isSelected ? meta.gradient : 'rgba(255,255,255,0.02)',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.2s',
                      transform: isSelected ? 'scale(1.02)' : 'scale(1)',
                    }}
                  >
                    <div style={{ fontSize: '1.6rem', marginBottom: '0.35rem' }}>{meta.emoji}</div>
                    <div style={{ fontWeight: 700, fontSize: '0.9rem', color: isSelected ? meta.color : 'var(--text)', marginBottom: '0.2rem' }}>
                      {bp.company_name}
                    </div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: 1.3 }}>
                      {bp.platform_name}
                    </div>
                    <div style={{ marginTop: '0.5rem', fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                      {bp.duration_minutes} min · {bp.sections?.length || 0} sections
                    </div>
                  </button>
                );
              })}
            </div>

            <form onSubmit={handleCreateFromBlueprint}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '0.75rem', marginBottom: '1rem' }}>
                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label">Assessment Title</label>
                  <input
                    type="text"
                    className="form-input"
                    value={blueprintTitle}
                    onChange={(e) => setBlueprintTitle(e.target.value)}
                    placeholder="e.g. TCS NQT — Batch 2027"
                    required
                  />
                </div>
                <div className="form-group" style={{ margin: 0, minWidth: '120px' }}>
                  <label className="form-label">Drive Window</label>
                  <select
                    className="form-select"
                    value={blueprintValidityHours}
                    onChange={(e) => setBlueprintValidityHours(Number(e.target.value))}
                  >
                    <option value={24}>24 hours</option>
                    <option value={48}>48 hours</option>
                    <option value={72}>3 days</option>
                    <option value={168}>7 days</option>
                    <option value={720}>30 days</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <button type="button" className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setShowBlueprintModal(false)}>
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ flex: 2 }}
                  disabled={isCreatingBlueprint || !selectedBlueprint}
                >
                  {isCreatingBlueprint ? 'Creating...' : `🚀 Create ${selectedBlueprint?.company_name || ''} Assessment`}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Create from scratch modal ─────────────────────────────────────────────── */}
      {showCreateModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(6px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 100, padding: '1rem',
        }}>
          <div className="card" style={{ maxWidth: '480px', width: '100%', padding: '2rem' }}>
            <h3 style={{ marginBottom: '0.5rem' }}>Create Technical Assessment</h3>
            <p style={{ fontSize: '0.85rem', marginBottom: '1.2rem', color: 'var(--text-muted)' }}>
              Set up initial exam parameters before attaching questions.
            </p>

            {error && (
              <div className="alert alert-error"><span>{error}</span></div>
            )}

            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label className="form-label">Assessment Title *</label>
                <input
                  type="text" className="form-input"
                  placeholder="e.g. Senior Backend Engineer Challenge"
                  value={title} onChange={handleTitleChange} required
                />
              </div>

              <div className="form-group">
                <label className="form-label">URL Slug *</label>
                <input
                  type="text" className="form-input"
                  placeholder="senior-backend-challenge"
                  value={slug}
                  onChange={(e) => setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ''))}
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Duration (Minutes)</label>
                  <input type="number" className="form-input" min={5} max={300} value={duration}
                    onChange={(e) => setDuration(Number(e.target.value))} required />
                </div>
                <div className="form-group">
                  <label className="form-label">Passing Score (%)</label>
                  <input type="number" className="form-input" min={0} max={100} value={passingScore}
                    onChange={(e) => setPassingScore(Number(e.target.value))} required />
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" style={{ flex: 1 }}
                  onClick={() => setShowCreateModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }} disabled={isCreating}>
                  {isCreating ? 'Creating...' : 'Continue to Builder'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Invite Candidate Modal ─────────────────────────────────────────────────── */}
      {inviteModalAss && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(6px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 100, padding: '1rem',
        }}>
          <div className="card" style={{ maxWidth: '500px', width: '100%', padding: '2rem' }}>
            <h3 style={{ marginBottom: '0.5rem' }}>Invite Candidate</h3>
            <p style={{ fontSize: '0.85rem', marginBottom: '1.2rem', color: 'var(--text-muted)' }}>
              Generate a secure, one-time link for <strong>{inviteModalAss.title}</strong>
            </p>

            {!generatedLink ? (
              <form onSubmit={handleGenerateInvite}>
                <div className="form-group">
                  <label className="form-label">Candidate Work Email *</label>
                  <input type="email" className="form-input" placeholder="candidate@example.com"
                    value={inviteEmail} onChange={(e) => setInviteEmail(e.target.value)} required />
                </div>
                <div className="form-group">
                  <label className="form-label">Candidate Full Name (Optional)</label>
                  <input type="text" className="form-input" placeholder="Alex Smith"
                    value={inviteName} onChange={(e) => setInviteName(e.target.value)} />
                </div>
                <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem' }}>
                  <button type="button" className="btn btn-secondary" style={{ flex: 1 }}
                    onClick={() => setInviteModalAss(null)}>Cancel</button>
                  <button type="submit" className="btn btn-primary" style={{ flex: 1 }} disabled={isInviting}>
                    {isInviting ? 'Generating...' : 'Create Invite Link'}
                  </button>
                </div>
              </form>
            ) : (
              <div>
                <div className="alert alert-success" style={{ marginBottom: '1rem' }}>
                  <CheckCircle2 size={16} />
                  <span>Unique candidate test link generated!</span>
                </div>
                <div className="form-group">
                  <label className="form-label">One-Time Test URL</label>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <input type="text" className="form-input" value={generatedLink} readOnly
                      style={{ fontSize: '0.85rem', fontFamily: 'var(--font-mono)' }} />
                    <button type="button" className="btn btn-primary" onClick={copyToClipboard}
                      style={{ padding: '0.6rem 1rem' }}>
                      {copied ? <Check size={16} /> : <Copy size={16} />}
                    </button>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem' }}>
                  <a href={generatedLink} target="_blank" rel="noopener noreferrer"
                    className="btn btn-secondary" style={{ flex: 1 }}>
                    <Play size={15} /> Test Exam View
                  </a>
                  <button type="button" className="btn btn-primary" style={{ flex: 1 }}
                    onClick={() => setInviteModalAss(null)}>Done</button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Resume Analysis Intelligence Modal */}
      {showResumeModal && <ResumeAnalysisModal onClose={() => setShowResumeModal(false)} />}
    </div>
  );
};
