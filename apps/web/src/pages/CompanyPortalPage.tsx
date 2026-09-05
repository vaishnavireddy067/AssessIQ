import React, { useEffect, useState } from 'react';
import { apiRequest } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { 
  Building, Key, Webhook, Shield, Users, Award, 
  CheckCircle2, AlertTriangle, Copy, Check, Plus, Trash2, 
  RefreshCw, Send, ExternalLink, Download, Sparkles, Layers,
  ChevronRight, Lock, CheckCircle, BarChart3, HelpCircle, ArrowUpRight
} from 'lucide-react';

export const CompanyPortalPage: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'overview' | 'profile' | 'api-keys' | 'webhooks' | 'sso' | 'candidates' | 'subscription'>('overview');

  // State
  const [company, setCompany] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [apiKeys, setApiKeys] = useState<any[]>([]);
  const [webhooks, setWebhooks] = useState<any[]>([]);
  const [ssoConfig, setSsoConfig] = useState<any>(null);
  const [candidates, setCandidates] = useState<any[]>([]);
  const [planUsage, setPlanUsage] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Notifications
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // API Key creation
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyExpiry, setNewKeyExpiry] = useState(90);
  const [createdKeySecret, setCreatedKeySecret] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState(false);
  const [isGeneratingKey, setIsGeneratingKey] = useState(false);

  // Webhook creation
  const [showWebhookModal, setShowWebhookModal] = useState(false);
  const [webhookUrl, setWebhookUrl] = useState('');
  const [selectedEvents, setSelectedEvents] = useState<string[]>(['candidate.submitted', 'proctoring.flagged']);
  const [isSavingWebhook, setIsSavingWebhook] = useState(false);
  const [testWebhookResult, setTestWebhookResult] = useState<any | null>(null);
  const [testingWebhookId, setTestingWebhookId] = useState<string | null>(null);

  // Company profile edit form
  const [companyForm, setCompanyForm] = useState({
    name: '',
    domain: '',
    website: '',
    industry: 'Technology',
    size: '50-200 employees',
    logo_url: '',
  });
  const [isSavingProfile, setIsSavingProfile] = useState(false);

  // SSO Form
  const [ssoForm, setSsoForm] = useState({
    provider_type: 'SAML',
    idp_entity_id: '',
    idp_sso_url: '',
    idp_x509_cert: '',
    oidc_client_id: '',
    oidc_client_secret: '',
    oidc_issuer: '',
    is_active: false,
  });
  const [isSavingSSO, setIsSavingSSO] = useState(false);

  // Candidate Directory search/filter
  const [candidateSearch, setCandidateSearch] = useState('');

  // Upgrade Modal
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [upgradePlan, setUpgradePlan] = useState('GROWTH');
  const [upgradeNotes, setUpgradeNotes] = useState('');
  const [isSubmittingUpgrade, setIsSubmittingUpgrade] = useState(false);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const loadAllData = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const [compRes, statsRes, keysRes, whRes, ssoRes, candRes, planRes] = await Promise.allSettled([
        apiRequest('/companies/me'),
        apiRequest('/companies/me/stats'),
        apiRequest('/companies/me/api-keys'),
        apiRequest('/companies/me/webhooks'),
        apiRequest('/companies/me/sso'),
        apiRequest('/companies/me/candidates'),
        apiRequest('/companies/me/plan-usage'),
      ]);

      if (compRes.status === 'fulfilled' && compRes.value) {
        setCompany(compRes.value);
        setCompanyForm({
          name: compRes.value.name || '',
          domain: compRes.value.domain || '',
          website: compRes.value.website || '',
          industry: compRes.value.industry || 'Technology',
          size: compRes.value.size || '50-200 employees',
          logo_url: compRes.value.logo_url || '',
        });
      }
      if (statsRes.status === 'fulfilled') setStats(statsRes.value);
      if (keysRes.status === 'fulfilled') setApiKeys(keysRes.value || []);
      if (whRes.status === 'fulfilled') setWebhooks(whRes.value || []);
      if (ssoRes.status === 'fulfilled' && ssoRes.value) {
        setSsoConfig(ssoRes.value);
        setSsoForm({
          provider_type: ssoRes.value.provider_type || 'SAML',
          idp_entity_id: ssoRes.value.idp_entity_id || '',
          idp_sso_url: ssoRes.value.idp_sso_url || '',
          idp_x509_cert: ssoRes.value.idp_x509_cert || '',
          oidc_client_id: ssoRes.value.oidc_client_id || '',
          oidc_client_secret: '',
          oidc_issuer: ssoRes.value.oidc_issuer || '',
          is_active: ssoRes.value.is_active || false,
        });
      }
      if (candRes.status === 'fulfilled') setCandidates(candRes.value || []);
      if (planRes.status === 'fulfilled') setPlanUsage(planRes.value);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load company workspace information');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  // Save Company Profile
  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSavingProfile(true);
    try {
      const updated = await apiRequest('/companies/me', {
        method: 'PUT',
        body: JSON.stringify(companyForm),
      });
      setCompany(updated);
      showToast('Organization settings updated successfully!');
    } catch (err: any) {
      alert(err.message || 'Failed to update company profile');
    } finally {
      setIsSavingProfile(false);
    }
  };

  // Generate API Key
  const handleCreateApiKey = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsGeneratingKey(true);
    try {
      const res = await apiRequest('/companies/me/api-keys', {
        method: 'POST',
        body: JSON.stringify({
          name: newKeyName,
          expires_in_days: Number(newKeyExpiry),
        }),
      });
      setCreatedKeySecret(res.raw_key);
      const updatedKeys = await apiRequest('/companies/me/api-keys');
      setApiKeys(updatedKeys);
      showToast('API Key generated successfully!');
    } catch (err: any) {
      alert(err.message || 'Failed to create API key');
    } finally {
      setIsGeneratingKey(false);
    }
  };

  // Revoke API Key
  const handleRevokeKey = async (keyId: string) => {
    if (!confirm('Are you sure you want to revoke this API key? External ATS integrations using this key will immediately fail.')) return;
    try {
      await apiRequest(`/companies/me/api-keys/${keyId}`, { method: 'DELETE' });
      setApiKeys(apiKeys.filter((k) => k.id !== keyId));
      showToast('API key revoked successfully.');
    } catch (err: any) {
      alert(err.message || 'Failed to revoke API key');
    }
  };

  // Save Webhook
  const handleCreateWebhook = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSavingWebhook(true);
    try {
      await apiRequest('/companies/me/webhooks', {
        method: 'POST',
        body: JSON.stringify({
          url: webhookUrl,
          events: selectedEvents,
        }),
      });
      setShowWebhookModal(false);
      setWebhookUrl('');
      const updatedWh = await apiRequest('/companies/me/webhooks');
      setWebhooks(updatedWh);
      showToast('Webhook endpoint registered!');
    } catch (err: any) {
      alert(err.message || 'Failed to register webhook');
    } finally {
      setIsSavingWebhook(false);
    }
  };

  // Delete Webhook
  const handleDeleteWebhook = async (webhookId: string) => {
    if (!confirm('Are you sure you want to remove this webhook endpoint?')) return;
    try {
      await apiRequest(`/companies/me/webhooks/${webhookId}`, { method: 'DELETE' });
      setWebhooks(webhooks.filter((w) => w.id !== webhookId));
      showToast('Webhook endpoint removed.');
    } catch (err: any) {
      alert(err.message || 'Failed to delete webhook');
    }
  };

  // Test Webhook
  const handleTestWebhook = async (webhookId: string) => {
    setTestingWebhookId(webhookId);
    setTestWebhookResult(null);
    try {
      const res = await apiRequest(`/companies/me/webhooks/${webhookId}/test`, { method: 'POST' });
      setTestWebhookResult(res);
      showToast('Test payload dispatched successfully!');
    } catch (err: any) {
      alert(err.message || 'Test webhook dispatch failed');
    } finally {
      setTestingWebhookId(null);
    }
  };

  // Save SSO
  const handleSaveSSO = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSavingSSO(true);
    try {
      const res = await apiRequest('/companies/me/sso', {
        method: 'PUT',
        body: JSON.stringify(ssoForm),
      });
      setSsoConfig(res);
      showToast('SSO Configuration saved successfully!');
    } catch (err: any) {
      alert(err.message || 'Failed to save SSO config');
    } finally {
      setIsSavingSSO(false);
    }
  };

  // Submit Upgrade Request
  const handleUpgradeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmittingUpgrade(true);
    try {
      const res = await apiRequest('/companies/me/upgrade-request', {
        method: 'POST',
        body: JSON.stringify({
          requested_plan: upgradePlan,
          notes: upgradeNotes,
        }),
      });
      setShowUpgradeModal(false);
      alert(res.message || 'Upgrade request submitted!');
      showToast('Upgrade request submitted for review!');
    } catch (err: any) {
      alert(err.message || 'Failed to submit upgrade request');
    } finally {
      setIsSubmittingUpgrade(false);
    }
  };

  // Filtered candidates
  const filteredCandidates = candidates.filter((c) => {
    const q = candidateSearch.toLowerCase();
    return (
      c.email?.toLowerCase().includes(q) ||
      c.full_name?.toLowerCase().includes(q) ||
      c.latest_assessment_title?.toLowerCase().includes(q)
    );
  });

  // Export Candidate CSV
  const handleExportCandidateCSV = () => {
    if (candidates.length === 0) {
      alert('No candidates to export');
      return;
    }
    const headers = ['Candidate ID', 'Email', 'Full Name', 'Assessment', 'Status', 'Score', 'Percentage', 'Proctoring Trust Score', 'Flagged', 'Created At'];
    const rows = candidates.map(c => [
      c.id,
      `"${c.email}"`,
      `"${c.full_name || ''}"`,
      `"${c.latest_assessment_title || 'N/A'}"`,
      c.latest_status || 'NOT_STARTED',
      c.latest_score !== null ? c.latest_score : 'N/A',
      c.latest_percentage !== null ? `${c.latest_percentage}%` : 'N/A',
      c.latest_integrity_score !== null ? `${c.latest_integrity_score}%` : 'N/A',
      c.is_flagged ? 'FLAGGED' : 'CLEAN',
      new Date(c.created_at).toISOString()
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `AssessIQ_${company?.slug || 'company'}_talent_pool.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast('Candidate talent pool exported to CSV!');
  };

  if (isLoading) {
    return (
      <div style={{ padding: '4rem 2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        <RefreshCw size={28} className="spin" style={{ margin: '0 auto 1rem', display: 'block', color: 'var(--primary)' }} />
        <p>Loading enterprise organization workspace...</p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1240px', margin: '2rem auto', padding: '0 1.5rem' }}>
      {/* Toast banner */}
      {toastMessage && (
        <div style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          backgroundColor: '#10B981',
          color: '#FFF',
          padding: '0.8rem 1.5rem',
          borderRadius: '10px',
          boxShadow: '0 8px 30px rgba(0,0,0,0.4)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          gap: '0.6rem',
          fontWeight: 600,
          animation: 'fadeIn 0.3s ease-out'
        }}>
          <CheckCircle size={18} /> {toastMessage}
        </div>
      )}

      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '2rem',
        flexWrap: 'wrap',
        gap: '1rem',
        paddingBottom: '1.5rem',
        borderBottom: '1px solid var(--border-color)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            width: '56px',
            height: '56px',
            borderRadius: '14px',
            background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(6, 182, 212, 0.2))',
            border: '1px solid rgba(99, 102, 241, 0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--primary)'
          }}>
            <Building size={30} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <h1 style={{ fontSize: '1.9rem', fontWeight: 800 }}>{company?.name || 'Company Hub'}</h1>
              <span className={`badge ${
                company?.plan === 'ENTERPRISE' ? 'badge-primary' :
                company?.plan === 'GROWTH' ? 'badge-warning' : 'badge-secondary'
              }`} style={{ fontSize: '0.75rem', padding: '0.2rem 0.6rem' }}>
                {company?.plan || 'STARTER'} TIER
              </span>
            </div>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
              Tenant Slug: <code style={{ color: 'var(--secondary)' }}>{company?.slug}</code> • {company?.industry || 'Enterprise'}
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button
            onClick={() => setShowUpgradeModal(true)}
            className="btn btn-primary btn-sm"
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
          >
            <Sparkles size={16} /> Manage Subscription & Upgrades
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div style={{
        display: 'flex',
        gap: '0.5rem',
        overflowX: 'auto',
        paddingBottom: '0.75rem',
        marginBottom: '2rem',
        borderBottom: '1px solid var(--border-color)'
      }}>
        {[
          { id: 'overview', label: 'Company Overview', icon: BarChart3 },
          { id: 'profile', label: 'Organization Profile', icon: Building },
          { id: 'api-keys', label: 'API Keys & ATS Integrations', icon: Key, count: apiKeys.length },
          { id: 'webhooks', label: 'Webhooks Dispatcher', icon: Webhook, count: webhooks.length },
          { id: 'sso', label: 'Enterprise SSO (SAML/OIDC)', icon: Shield },
          { id: 'candidates', label: 'Talent Pool Directory', icon: Users, count: candidates.length },
          { id: 'subscription', label: 'Plan & Usage Quotas', icon: Award },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.65rem 1.1rem',
                borderRadius: '8px',
                border: 'none',
                backgroundColor: isActive ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                color: isActive ? 'var(--primary)' : 'var(--text-muted)',
                fontWeight: isActive ? 700 : 500,
                fontSize: '0.9rem',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                transition: 'all 0.2s ease',
                borderBottom: isActive ? '2px solid var(--primary)' : '2px solid transparent'
              }}
            >
              <Icon size={16} />
              {tab.label}
              {tab.count !== undefined && (
                <span style={{
                  fontSize: '0.7rem',
                  padding: '0.1rem 0.45rem',
                  borderRadius: '12px',
                  backgroundColor: isActive ? 'var(--primary)' : 'rgba(255,255,255,0.08)',
                  color: isActive ? '#FFF' : 'var(--text-muted)'
                }}>
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* ── TAB 1: OVERVIEW ── */}
      {activeTab === 'overview' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Top KPI Cards */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))',
            gap: '1.25rem',
          }}>
            <div className="card card-hover" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '12px',
                background: 'rgba(99, 102, 241, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--primary)',
              }}>
                <Layers size={24} />
              </div>
              <div>
                <div style={{ fontSize: '1.75rem', fontWeight: 800 }}>{stats?.total_assessments || 0}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Created Assessments</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--success)' }}>{stats?.published_assessments || 0} Published Live</div>
              </div>
            </div>

            <div className="card card-hover" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '12px',
                background: 'rgba(6, 182, 212, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--secondary)',
              }}>
                <Users size={24} />
              </div>
              <div>
                <div style={{ fontSize: '1.75rem', fontWeight: 800 }}>{stats?.total_invitations || 0}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Candidates Invited</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{stats?.completed_attempts || 0} Completed Tests</div>
              </div>
            </div>

            <div className="card card-hover" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '12px',
                background: 'rgba(16, 185, 129, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--success)',
              }}>
                <Award size={24} />
              </div>
              <div>
                <div style={{ fontSize: '1.75rem', fontWeight: 800 }}>{stats?.average_score || 0}%</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Average Candidate Score</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Benchmark: 65%</div>
              </div>
            </div>

            <div className="card card-hover" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '12px',
                background: 'rgba(239, 68, 68, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--danger)',
              }}>
                <Shield size={24} />
              </div>
              <div>
                <div style={{ fontSize: '1.75rem', fontWeight: 800 }}>{stats?.flagged_attempts || 0}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Integrity Flags Detected</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>AI Proctoring Active</div>
              </div>
            </div>
          </div>

          {/* Quick Actions & Usage summary */}
          <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '1.5rem' }}>
            <div className="card">
              <h3 style={{ fontSize: '1.15rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Building size={18} color="var(--primary)" /> Enterprise Workspace Quick Actions
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <button
                  onClick={() => setActiveTab('api-keys')}
                  style={{
                    padding: '1.1rem',
                    borderRadius: '10px',
                    backgroundColor: 'rgba(255,255,255,0.02)',
                    border: '1px solid var(--border-color)',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'flex-start',
                    gap: '0.5rem',
                    cursor: 'pointer',
                    textAlign: 'left'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                    <Key size={20} color="var(--primary)" />
                    <ChevronRight size={16} color="var(--text-dim)" />
                  </div>
                  <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>Connect ATS APIs</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Generate keys for Workable, Greenhouse & Lever</div>
                </button>

                <button
                  onClick={() => setActiveTab('webhooks')}
                  style={{
                    padding: '1.1rem',
                    borderRadius: '10px',
                    backgroundColor: 'rgba(255,255,255,0.02)',
                    border: '1px solid var(--border-color)',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'flex-start',
                    gap: '0.5rem',
                    cursor: 'pointer',
                    textAlign: 'left'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                    <Webhook size={20} color="var(--secondary)" />
                    <ChevronRight size={16} color="var(--text-dim)" />
                  </div>
                  <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>Configure Webhooks</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Real-time event webhooks on test submissions</div>
                </button>

                <button
                  onClick={() => setActiveTab('candidates')}
                  style={{
                    padding: '1.1rem',
                    borderRadius: '10px',
                    backgroundColor: 'rgba(255,255,255,0.02)',
                    border: '1px solid var(--border-color)',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'flex-start',
                    gap: '0.5rem',
                    cursor: 'pointer',
                    textAlign: 'left'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                    <Users size={20} color="var(--success)" />
                    <ChevronRight size={16} color="var(--text-dim)" />
                  </div>
                  <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>Candidate Directory</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Search all candidates and export to CSV</div>
                </button>

                <button
                  onClick={() => setActiveTab('sso')}
                  style={{
                    padding: '1.1rem',
                    borderRadius: '10px',
                    backgroundColor: 'rgba(255,255,255,0.02)',
                    border: '1px solid var(--border-color)',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'flex-start',
                    gap: '0.5rem',
                    cursor: 'pointer',
                    textAlign: 'left'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                    <Shield size={20} color="var(--warning)" />
                    <ChevronRight size={16} color="var(--text-dim)" />
                  </div>
                  <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>Enterprise SSO Setup</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Configure SAML 2.0 / Okta / Azure AD</div>
                </button>
              </div>
            </div>

            {/* Quota Gauge */}
            <div className="card">
              <h3 style={{ fontSize: '1.15rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Award size={18} color="var(--primary)" /> Monthly Candidate Quota
              </h3>
              <div style={{ marginBottom: '1.25rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Invites Used:</span>
                  <span style={{ fontWeight: 700 }}>{stats?.candidates_quota_used || 0} / {stats?.candidates_quota_limit || 50}</span>
                </div>
                <div style={{ width: '100%', height: '8px', backgroundColor: 'rgba(255,255,255,0.08)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{
                    height: '100%',
                    width: `${Math.min(100, Math.round(((stats?.candidates_quota_used || 0) / (stats?.candidates_quota_limit || 50)) * 100))}%`,
                    backgroundColor: 'var(--primary)',
                    borderRadius: '4px'
                  }} />
                </div>
              </div>

              <div style={{
                padding: '1rem',
                borderRadius: '8px',
                backgroundColor: 'rgba(99, 102, 241, 0.08)',
                border: '1px solid rgba(99, 102, 241, 0.2)',
                fontSize: '0.85rem'
              }}>
                <div style={{ fontWeight: 600, color: 'var(--primary)', marginBottom: '0.25rem' }}>
                  Need more candidate volume?
                </div>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '0.75rem' }}>
                  Upgrade to our Growth or Enterprise tier for unlimited candidate slots, AI proctoring, and ATS integrations.
                </p>
                <button
                  onClick={() => setShowUpgradeModal(true)}
                  className="btn btn-secondary btn-sm"
                  style={{ width: '100%' }}
                >
                  Upgrade Plan Tier
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── TAB 2: ORGANIZATION PROFILE ── */}
      {activeTab === 'profile' && (
        <div className="card" style={{ maxWidth: '800px' }}>
          <h2 style={{ fontSize: '1.35rem', marginBottom: '0.5rem' }}>Organization Profile & Branding</h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
            Customize your company profile, industry classification, and candidate-facing branding.
          </p>

          <form onSubmit={handleSaveProfile} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Company Legal Name *</label>
                <input
                  type="text"
                  className="form-input"
                  value={companyForm.name}
                  onChange={(e) => setCompanyForm({ ...companyForm, name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Organization Slug (Immutable)</label>
                <input
                  type="text"
                  className="form-input"
                  value={company?.slug || ''}
                  disabled
                  style={{ opacity: 0.6, cursor: 'not-allowed' }}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Corporate Website</label>
                <input
                  type="url"
                  className="form-input"
                  placeholder="https://acmecorp.com"
                  value={companyForm.website}
                  onChange={(e) => setCompanyForm({ ...companyForm, website: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Corporate Domain</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="acmecorp.com"
                  value={companyForm.domain}
                  onChange={(e) => setCompanyForm({ ...companyForm, domain: e.target.value })}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Industry Classification</label>
                <select
                  className="form-select"
                  value={companyForm.industry}
                  onChange={(e) => setCompanyForm({ ...companyForm, industry: e.target.value })}
                >
                  <option value="Technology">Technology & Software</option>
                  <option value="Finance">Financial Services & Banking</option>
                  <option value="Healthcare">Healthcare & BioTech</option>
                  <option value="E-Commerce">E-Commerce & Retail</option>
                  <option value="Consulting">Consulting & Professional Services</option>
                  <option value="Education">Education & EdTech</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Company Size</label>
                <select
                  className="form-select"
                  value={companyForm.size}
                  onChange={(e) => setCompanyForm({ ...companyForm, size: e.target.value })}
                >
                  <option value="1-20 employees">1 - 20 employees</option>
                  <option value="20-100 employees">20 - 100 employees</option>
                  <option value="100-500 employees">100 - 500 employees</option>
                  <option value="500-2000 employees">500 - 2,000 employees</option>
                  <option value="2000+ employees">2,000+ employees</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Custom Logo URL (Shown on candidate exam screen)</label>
              <input
                type="url"
                className="form-input"
                placeholder="https://assets.acmecorp.com/logo.svg"
                value={companyForm.logo_url}
                onChange={(e) => setCompanyForm({ ...companyForm, logo_url: e.target.value })}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1rem' }}>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isSavingProfile}
              >
                {isSavingProfile ? 'Saving Changes...' : 'Save Organization Profile'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* ── TAB 3: API KEYS & ATS INTEGRATION ── */}
      {activeTab === 'api-keys' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <h2 style={{ fontSize: '1.35rem', marginBottom: '0.35rem' }}>Programmatic API Keys</h2>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  Authenticate external ATS platforms (Workable, Greenhouse, Lever) to trigger assessment invites and pull candidate scorecards.
                </p>
              </div>
              <button
                onClick={() => {
                  setShowKeyModal(true);
                  setCreatedKeySecret(null);
                  setNewKeyName('');
                }}
                className="btn btn-primary btn-sm"
                style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
              >
                <Plus size={16} /> Generate New API Key
              </button>
            </div>

            {/* API Keys Table */}
            {apiKeys.length === 0 ? (
              <div style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-muted)', border: '1px dashed var(--border-color)', borderRadius: '8px' }}>
                <Key size={32} style={{ margin: '0 auto 0.75rem', opacity: 0.5 }} />
                <p style={{ fontWeight: 600 }}>No API Keys generated yet.</p>
                <p style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>Generate an API key to integrate with Greenhouse, Lever, or custom microservices.</p>
              </div>
            ) : (
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Key Name</th>
                      <th>Key Prefix</th>
                      <th>Status</th>
                      <th>Last Used</th>
                      <th>Expires</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {apiKeys.map((k) => (
                      <tr key={k.id}>
                        <td style={{ fontWeight: 600 }}>{k.name}</td>
                        <td>
                          <code style={{ color: 'var(--secondary)', fontFamily: 'var(--font-mono)' }}>{k.prefix}</code>
                        </td>
                        <td>
                          <span className={`badge ${k.is_active ? 'badge-success' : 'badge-danger'}`} style={{ fontSize: '0.7rem' }}>
                            {k.is_active ? 'Active' : 'Revoked'}
                          </span>
                        </td>
                        <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                          {k.last_used_at ? new Date(k.last_used_at).toLocaleDateString() : 'Never'}
                        </td>
                        <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                          {k.expires_at ? new Date(k.expires_at).toLocaleDateString() : 'Never'}
                        </td>
                        <td>
                          <button
                            onClick={() => handleRevokeKey(k.id)}
                            className="btn btn-secondary btn-sm"
                            style={{ color: 'var(--danger)', borderColor: 'rgba(239, 68, 68, 0.3)' }}
                            title="Revoke API Key"
                          >
                            <Trash2 size={14} /> Revoke
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Quick Integration Guide / Code snippets */}
          <div className="card">
            <h3 style={{ fontSize: '1.15rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <HelpCircle size={18} color="var(--primary)" /> ATS Integration Code Snippet
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
              Pass your generated API key in the <code>Authorization</code> header to invite candidates or fetch completed test evaluations.
            </p>

            <pre style={{
              backgroundColor: 'rgba(0,0,0,0.5)',
              padding: '1.25rem',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
              overflowX: 'auto',
              fontSize: '0.8rem',
              color: '#38BDF8',
              fontFamily: 'var(--font-mono)'
            }}>
{`# 1. Invite Candidate from ATS (Greenhouse / Lever / Workable webhook):
curl -X POST https://api.assessiq.com/public/v1/assessments/{ASSESSMENT_ID}/invite \\
  -H "Authorization: Bearer YOUR_AIQ_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "candidate_email": "candidate@example.com",
    "candidate_name": "Jane Doe",
    "job_role": "Senior Full-Stack Engineer"
  }'

# 2. Fetch Candidate Result & Proctoring Risk Score:
curl -X GET https://api.assessiq.com/public/v1/results/{ATTEMPT_ID} \\
  -H "Authorization: Bearer YOUR_AIQ_API_KEY"`}
            </pre>
          </div>
        </div>
      )}

      {/* ── TAB 4: WEBHOOKS DISPATCHER ── */}
      {activeTab === 'webhooks' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <h2 style={{ fontSize: '1.35rem', marginBottom: '0.35rem' }}>Real-time Webhook Subscriptions</h2>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  Dispatch JSON payloads to your HR system whenever a candidate completes a test or an integrity flag is triggered.
                </p>
              </div>
              <button
                onClick={() => setShowWebhookModal(true)}
                className="btn btn-primary btn-sm"
                style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
              >
                <Plus size={16} /> Add Webhook Destination
              </button>
            </div>

            {/* Webhooks Table */}
            {webhooks.length === 0 ? (
              <div style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-muted)', border: '1px dashed var(--border-color)', borderRadius: '8px' }}>
                <Webhook size={32} style={{ margin: '0 auto 0.75rem', opacity: 0.5 }} />
                <p style={{ fontWeight: 600 }}>No webhook endpoints registered yet.</p>
                <p style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>Subscribe to candidate completion events and receive scorecards in real-time.</p>
              </div>
            ) : (
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Endpoint URL</th>
                      <th>Subscribed Events</th>
                      <th>Signing Secret</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {webhooks.map((w) => (
                      <tr key={w.id}>
                        <td>
                          <code style={{ color: 'var(--text-main)', fontSize: '0.85rem' }}>{w.url}</code>
                        </td>
                        <td>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
                            {w.events?.map((ev: string) => (
                              <span key={ev} className="badge badge-primary" style={{ fontSize: '0.65rem' }}>
                                {ev}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td>
                          <code style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>
                            {w.secret_key ? `${w.secret_key.substring(0, 10)}...` : '••••••••'}
                          </code>
                        </td>
                        <td>
                          <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>Active</span>
                        </td>
                        <td>
                          <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <button
                              onClick={() => handleTestWebhook(w.id)}
                              disabled={testingWebhookId === w.id}
                              className="btn btn-secondary btn-sm"
                              style={{ padding: '0.3rem 0.6rem' }}
                              title="Send Test Ping"
                            >
                              <Send size={13} /> {testingWebhookId === w.id ? 'Testing...' : 'Test'}
                            </button>
                            <button
                              onClick={() => handleDeleteWebhook(w.id)}
                              className="btn btn-secondary btn-sm"
                              style={{ color: 'var(--danger)', padding: '0.3rem 0.6rem' }}
                              title="Delete Webhook"
                            >
                              <Trash2 size={13} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Live Test Payload Preview */}
          {testWebhookResult && (
            <div className="card" style={{ border: '1px solid rgba(16, 185, 129, 0.4)', backgroundColor: 'rgba(16, 185, 129, 0.03)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '1rem', color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <CheckCircle2 size={18} /> Test Webhook Payload Dispatched
                </h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {new Date(testWebhookResult.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <pre style={{
                backgroundColor: 'rgba(0,0,0,0.5)',
                padding: '1rem',
                borderRadius: '6px',
                fontSize: '0.8rem',
                color: '#A7F3D0',
                fontFamily: 'var(--font-mono)'
              }}>
                {JSON.stringify(testWebhookResult.payload_dispatched, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* ── TAB 5: ENTERPRISE SSO ── */}
      {activeTab === 'sso' && (
        <div className="card" style={{ maxWidth: '820px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <div>
              <h2 style={{ fontSize: '1.35rem', marginBottom: '0.35rem' }}>Enterprise Single Sign-On (SSO)</h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                Enforce corporate identity authentication with Okta, Microsoft Azure Active Directory, Google Workspace, or PingIdentity.
              </p>
            </div>
            <span className={`badge ${ssoForm.is_active ? 'badge-success' : 'badge-secondary'}`}>
              {ssoForm.is_active ? 'SSO ACTIVE' : 'SSO DISABLED'}
            </span>
          </div>

          <form onSubmit={handleSaveSSO} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div className="form-group">
              <label className="form-label">Federation Protocol</label>
              <select
                className="form-select"
                value={ssoForm.provider_type}
                onChange={(e) => setSsoForm({ ...ssoForm, provider_type: e.target.value })}
              >
                <option value="SAML">SAML 2.0 (Okta, Azure AD, OneLogin)</option>
                <option value="OIDC">OpenID Connect (OIDC / OAuth 2.0)</option>
              </select>
            </div>

            {ssoForm.provider_type === 'SAML' ? (
              <>
                <div className="form-group">
                  <label className="form-label">Identity Provider Entity ID (Issuer URL)</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="https://sts.windows.net/acme-tenant-id/"
                    value={ssoForm.idp_entity_id}
                    onChange={(e) => setSsoForm({ ...ssoForm, idp_entity_id: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">IdP Single Sign-On URL</label>
                  <input
                    type="url"
                    className="form-input"
                    placeholder="https://login.microsoftonline.com/acme/saml2"
                    value={ssoForm.idp_sso_url}
                    onChange={(e) => setSsoForm({ ...ssoForm, idp_sso_url: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">X.509 Public Signing Certificate (PEM format)</label>
                  <textarea
                    className="form-textarea"
                    rows={4}
                    placeholder="-----BEGIN CERTIFICATE-----&#10;MIIC...&#10;-----END CERTIFICATE-----"
                    value={ssoForm.idp_x509_cert}
                    onChange={(e) => setSsoForm({ ...ssoForm, idp_x509_cert: e.target.value })}
                    style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}
                  />
                </div>
              </>
            ) : (
              <>
                <div className="form-group">
                  <label className="form-label">OIDC Client ID</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="0oa...okta_client_id"
                    value={ssoForm.oidc_client_id}
                    onChange={(e) => setSsoForm({ ...ssoForm, oidc_client_id: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">OIDC Issuer URL</label>
                  <input
                    type="url"
                    className="form-input"
                    placeholder="https://acme.okta.com/oauth2/default"
                    value={ssoForm.oidc_issuer}
                    onChange={(e) => setSsoForm({ ...ssoForm, oidc_issuer: e.target.value })}
                  />
                </div>
              </>
            )}

            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              padding: '1rem',
              borderRadius: '8px',
              backgroundColor: 'rgba(255,255,255,0.02)',
              border: '1px solid var(--border-color)'
            }}>
              <input
                type="checkbox"
                id="ssoActiveCheck"
                checked={ssoForm.is_active}
                onChange={(e) => setSsoForm({ ...ssoForm, is_active: e.target.checked })}
                style={{ width: '18px', height: '18px', cursor: 'pointer' }}
              />
              <label htmlFor="ssoActiveCheck" style={{ fontSize: '0.9rem', cursor: 'pointer', fontWeight: 600 }}>
                Enforce SSO for all organization recruiters and admins
              </label>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1rem' }}>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isSavingSSO}
              >
                {isSavingSSO ? 'Saving SSO Settings...' : 'Save SSO Configuration'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* ── TAB 6: CANDIDATE TALENT DIRECTORY ── */}
      {activeTab === 'candidates' && (
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <h2 style={{ fontSize: '1.35rem', marginBottom: '0.35rem' }}>Company Candidate Talent Directory</h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                Centralized talent pool of all candidates evaluated across your organization's assessments.
              </p>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
              <input
                type="text"
                className="form-input"
                placeholder="Search by candidate name or email..."
                value={candidateSearch}
                onChange={(e) => setCandidateSearch(e.target.value)}
                style={{ width: '280px', fontSize: '0.85rem' }}
              />
              <button
                onClick={handleExportCandidateCSV}
                className="btn btn-secondary btn-sm"
                style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
              >
                <Download size={15} /> Export Talent CSV
              </button>
            </div>
          </div>

          {filteredCandidates.length === 0 ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              <Users size={36} style={{ margin: '0 auto 0.75rem', opacity: 0.4 }} />
              <p style={{ fontWeight: 600 }}>No candidates found.</p>
              <p style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>Send test invitations to start populating your talent pool.</p>
            </div>
          ) : (
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Candidate</th>
                    <th>Latest Assessment</th>
                    <th>Status</th>
                    <th>Score</th>
                    <th>Integrity Trust</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCandidates.map((cand) => (
                    <tr key={cand.id}>
                      <td>
                        <div style={{ fontWeight: 600 }}>{cand.full_name || 'Unnamed Candidate'}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{cand.email}</div>
                      </td>
                      <td>
                        <span style={{ fontSize: '0.85rem' }}>
                          {cand.latest_assessment_title || <span style={{ color: 'var(--text-dim)' }}>None</span>}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${
                          cand.latest_status === 'SUBMITTED' ? 'badge-success' :
                          cand.latest_status === 'IN_PROGRESS' ? 'badge-primary' : 'badge-secondary'
                        }`} style={{ fontSize: '0.7rem' }}>
                          {cand.latest_status || 'INVITED'}
                        </span>
                      </td>
                      <td>
                        {cand.latest_percentage !== null ? (
                          <span style={{ fontWeight: 700, color: cand.latest_percentage >= 60 ? 'var(--success)' : 'var(--danger)' }}>
                            {cand.latest_percentage}%
                          </span>
                        ) : (
                          <span style={{ color: 'var(--text-dim)', fontSize: '0.8rem' }}>—</span>
                        )}
                      </td>
                      <td>
                        {cand.is_flagged ? (
                          <span className="badge badge-danger" style={{ fontSize: '0.65rem' }}>
                            <AlertTriangle size={11} style={{ marginRight: '3px' }} /> Flagged
                          </span>
                        ) : cand.latest_integrity_score !== null ? (
                          <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>
                            <CheckCircle2 size={11} style={{ marginRight: '3px' }} /> {cand.latest_integrity_score}% Trust
                          </span>
                        ) : (
                          <span style={{ color: 'var(--text-dim)', fontSize: '0.8rem' }}>—</span>
                        )}
                      </td>
                      <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {new Date(cand.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── TAB 7: SUBSCRIPTION & PLAN QUOTAS ── */}
      {activeTab === 'subscription' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Active Plan Overview */}
          <div className="card" style={{ background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(6, 182, 212, 0.08) 100%)', border: '1px solid rgba(99, 102, 241, 0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <span className="badge badge-primary" style={{ marginBottom: '0.5rem' }}>CURRENT SUBSCRIPTION</span>
                <h2 style={{ fontSize: '1.75rem', fontWeight: 800 }}>{company?.plan || 'STARTER'} TIER</h2>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  Active billing period renewal: {planUsage?.current_period_end ? new Date(planUsage.current_period_end).toLocaleDateString() : 'Monthly Cycle'}
                </p>
              </div>

              <button
                onClick={() => setShowUpgradeModal(true)}
                className="btn btn-primary"
                style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
              >
                <Sparkles size={16} /> Request Tier Upgrade
              </button>
            </div>
          </div>

          {/* Pricing Tiers Comparison Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
            {/* Starter */}
            <div className="card" style={{ borderColor: company?.plan === 'STARTER' ? 'var(--primary)' : 'var(--border-color)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '1.25rem' }}>Starter</h3>
                {company?.plan === 'STARTER' && <span className="badge badge-primary">CURRENT</span>}
              </div>
              <div style={{ fontSize: '1.85rem', fontWeight: 800, marginBottom: '1rem' }}>
                $199 <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 400 }}>/ mo</span>
              </div>
              <ul style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', fontSize: '0.85rem', color: 'var(--text-muted)', paddingLeft: '1.2rem', marginBottom: '1.5rem' }}>
                <li>Up to 50 candidate invitations / mo</li>
                <li>MCQ & Coding Sandboxes (Python, JS, C++)</li>
                <li>Standard Recruiter Scorecards</li>
                <li>Email Support</li>
              </ul>
            </div>

            {/* Growth */}
            <div className="card" style={{ borderColor: company?.plan === 'GROWTH' ? 'var(--primary)' : 'rgba(99, 102, 241, 0.4)', background: 'rgba(99, 102, 241, 0.03)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '1.25rem', color: 'var(--primary)' }}>Growth</h3>
                {company?.plan === 'GROWTH' && <span className="badge badge-primary">CURRENT</span>}
              </div>
              <div style={{ fontSize: '1.85rem', fontWeight: 800, marginBottom: '1rem' }}>
                $499 <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 400 }}>/ mo</span>
              </div>
              <ul style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', fontSize: '0.85rem', color: 'var(--text-muted)', paddingLeft: '1.2rem', marginBottom: '1.5rem' }}>
                <li>Up to 250 candidate invitations / mo</li>
                <li>AI Question Generator & Resume Parser</li>
                <li>AI Proctoring Intelligence (Camera/Mic)</li>
                <li>ATS Webhooks & Real-time Alerts</li>
                <li>Priority SLA Support</li>
              </ul>
            </div>

            {/* Enterprise */}
            <div className="card" style={{ borderColor: company?.plan === 'ENTERPRISE' ? 'var(--primary)' : 'rgba(6, 182, 212, 0.4)', background: 'rgba(6, 182, 212, 0.03)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '1.25rem', color: 'var(--secondary)' }}>Enterprise</h3>
                {company?.plan === 'ENTERPRISE' && <span className="badge badge-primary">CURRENT</span>}
              </div>
              <div style={{ fontSize: '1.85rem', fontWeight: 800, marginBottom: '1rem' }}>
                Custom <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 400 }}>annual SLA</span>
              </div>
              <ul style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', fontSize: '0.85rem', color: 'var(--text-muted)', paddingLeft: '1.2rem', marginBottom: '1.5rem' }}>
                <li>Unlimited candidate testing volume</li>
                <li>Dedicated ATS APIs (Greenhouse, Lever, Workable)</li>
                <li>Enterprise SAML 2.0 / OIDC SSO</li>
                <li>Leak Radar & Panel Review Studio</li>
                <li>Dedicated Customer Success Manager</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* ── MODAL: GENERATE API KEY ── */}
      {showKeyModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.75)',
          backdropFilter: 'blur(6px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: '1rem',
        }}>
          <div className="card" style={{ maxWidth: '500px', width: '100%', padding: '2rem' }}>
            <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Generate Programmatic API Key</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
              Create an API key for your external ATS integration or custom HR pipeline.
            </p>

            {createdKeySecret ? (
              <div>
                <div className="alert alert-warning" style={{ marginBottom: '1rem' }}>
                  <AlertTriangle size={18} />
                  <span>Copy this secret API key now. It will not be shown again!</span>
                </div>

                <div style={{
                  padding: '0.75rem 1rem',
                  borderRadius: '8px',
                  backgroundColor: 'rgba(0,0,0,0.6)',
                  border: '1px solid var(--border-color)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.85rem',
                  color: '#38BDF8',
                  wordBreak: 'break-all',
                  marginBottom: '1.5rem'
                }}>
                  <span>{createdKeySecret}</span>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(createdKeySecret);
                      setCopiedKey(true);
                      setTimeout(() => setCopiedKey(false), 2000);
                    }}
                    className="btn btn-secondary btn-sm"
                    style={{ marginLeft: '0.5rem' }}
                  >
                    {copiedKey ? <Check size={14} color="var(--success)" /> : <Copy size={14} />}
                  </button>
                </div>

                <button
                  onClick={() => {
                    setShowKeyModal(false);
                    setCreatedKeySecret(null);
                  }}
                  className="btn btn-primary"
                  style={{ width: '100%' }}
                >
                  I have saved this API Key
                </button>
              </div>
            ) : (
              <form onSubmit={handleCreateApiKey} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Key Description / Name *</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Greenhouse Production ATS"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Expiration *</label>
                  <select
                    className="form-select"
                    value={newKeyExpiry}
                    onChange={(e) => setNewKeyExpiry(Number(e.target.value))}
                  >
                    <option value={30}>30 Days</option>
                    <option value={90}>90 Days (Recommended)</option>
                    <option value={180}>180 Days</option>
                    <option value={365}>1 Year</option>
                  </select>
                </div>

                <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    style={{ flex: 1 }}
                    onClick={() => setShowKeyModal(false)}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary"
                    style={{ flex: 1 }}
                    disabled={isGeneratingKey}
                  >
                    {isGeneratingKey ? 'Generating...' : 'Create API Key'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* ── MODAL: ADD WEBHOOK ── */}
      {showWebhookModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.75)',
          backdropFilter: 'blur(6px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: '1rem',
        }}>
          <div className="card" style={{ maxWidth: '520px', width: '100%', padding: '2rem' }}>
            <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Add Webhook Destination</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
              AssessIQ will POST an HTTPS JSON payload to this URL when selected events occur.
            </p>

            <form onSubmit={handleCreateWebhook} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Destination HTTPS URL *</label>
                <input
                  type="url"
                  className="form-input"
                  placeholder="https://api.acmecorp.com/webhooks/assessiq"
                  value={webhookUrl}
                  onChange={(e) => setWebhookUrl(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Subscribed Events *</label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {[
                    { id: 'candidate.submitted', label: 'candidate.submitted (Candidate finishes test & scorecard calculated)' },
                    { id: 'proctoring.flagged', label: 'proctoring.flagged (Integrity alert triggered during proctoring)' },
                    { id: 'assessment.published', label: 'assessment.published (Assessment goes live)' }
                  ].map((ev) => (
                    <label key={ev.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={selectedEvents.includes(ev.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedEvents([...selectedEvents, ev.id]);
                          } else {
                            setSelectedEvents(selectedEvents.filter(x => x !== ev.id));
                          }
                        }}
                      />
                      <code>{ev.label}</code>
                    </label>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ flex: 1 }}
                  onClick={() => setShowWebhookModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ flex: 1 }}
                  disabled={isSavingWebhook}
                >
                  {isSavingWebhook ? 'Registering...' : 'Register Webhook'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── MODAL: UPGRADE REQUEST ── */}
      {showUpgradeModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.75)',
          backdropFilter: 'blur(6px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: '1rem',
        }}>
          <div className="card" style={{ maxWidth: '480px', width: '100%', padding: '2rem' }}>
            <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Upgrade Organization Subscription</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
              Scale your hiring pipeline with advanced AI generation, sensory proctoring, and custom ATS APIs.
            </p>

            <form onSubmit={handleUpgradeSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Desired Tier *</label>
                <select
                  className="form-select"
                  value={upgradePlan}
                  onChange={(e) => setUpgradePlan(e.target.value)}
                >
                  <option value="GROWTH">Growth ($499/mo — 250 candidates + AI Copilot)</option>
                  <option value="ENTERPRISE">Enterprise (Custom SLA — Unlimited candidates + SSO + Dedicated ATS)</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Estimated Monthly Candidate Volume / Requirements</label>
                <textarea
                  className="form-textarea"
                  rows={3}
                  placeholder="e.g. Expecting 300+ candidates for upcoming graduate hiring batch..."
                  value={upgradeNotes}
                  onChange={(e) => setUpgradeNotes(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ flex: 1 }}
                  onClick={() => setShowUpgradeModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ flex: 1 }}
                  disabled={isSubmittingUpgrade}
                >
                  {isSubmittingUpgrade ? 'Submitting...' : 'Submit Upgrade Request'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
