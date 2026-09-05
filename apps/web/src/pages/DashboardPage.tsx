import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiRequest } from '../api/client';
import { 
  Building, Users, UserPlus, ShieldAlert, Sparkles, 
  CheckCircle2, Clock, FileText, ChevronRight, Activity 
} from 'lucide-react';
import { CandidateDashboardPage } from './CandidateDashboardPage';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();

  // If the logged in user is purely a Candidate, render the Candidate Dashboard
  if (user?.roles.includes('CANDIDATE') && !user?.roles.includes('COMPANY_ADMIN') && !user?.roles.includes('SUPER_ADMIN')) {
    return <CandidateDashboardPage />;
  }

  const [company, setCompany] = useState<any>(null);
  const [teamMembers, setTeamMembers] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Invite user modal state
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [invitePassword, setInvitePassword] = useState('Welcome2026!');
  const [inviteRole, setInviteRole] = useState('RECRUITER');
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [isInviting, setIsInviting] = useState(false);

  const loadData = async () => {
    try {
      setIsLoading(true);
      if (user?.company_id) {
        const compRes = await apiRequest('/companies/me');
        setCompany(compRes);
      }
      const usersRes = await apiRequest('/users');
      setTeamMembers(usersRes);

      const logsRes = await apiRequest('/audit?limit=8');
      setAuditLogs(logsRes);
    } catch (err) {
      console.error('Error loading dashboard data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [user]);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setInviteError(null);
    setIsInviting(true);
    try {
      await apiRequest('/users', {
        method: 'POST',
        body: JSON.stringify({
          email: inviteEmail,
          password: invitePassword,
          role_name: inviteRole,
        }),
      });
      setShowInviteModal(false);
      setInviteEmail('');
      await loadData();
    } catch (err: any) {
      setInviteError(err.message || 'Failed to add team member');
    } finally {
      setIsInviting(false);
    }
  };

  if (isLoading) {
    return (
      <div style={{ padding: '3rem 2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        <p>Loading organization workspace...</p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '2rem auto', padding: '0 1.5rem' }}>
      {/* Workspace Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '2rem',
        flexWrap: 'wrap',
        gap: '1rem',
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.35rem' }}>
            <h1 style={{ fontSize: '1.85rem' }}>{company?.name || 'Workspace Dashboard'}</h1>
            {company?.plan && (
              <span className="badge badge-primary">{company.plan} PLAN</span>
            )}
          </div>
          <p style={{ fontSize: '0.95rem' }}>
            Organization Slug: <code style={{ color: 'var(--secondary)', fontFamily: 'var(--font-mono)' }}>{company?.slug || 'global'}</code>
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <a
            href="/company/settings"
            className="btn btn-secondary btn-sm"
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', textDecoration: 'none' }}
          >
            <Building size={16} color="var(--primary)" /> Company Portal & ATS Integrations
          </a>
          <button
            onClick={() => setShowInviteModal(true)}
            className="btn btn-primary btn-sm"
          >
            <UserPlus size={16} /> Add Team Member
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '1.25rem',
        marginBottom: '2rem',
      }}>
        <div className="card card-hover" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            width: '46px',
            height: '46px',
            borderRadius: '10px',
            background: 'rgba(99, 102, 241, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--primary)',
          }}>
            <Users size={24} />
          </div>
          <div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800 }}>{teamMembers.length}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Active Team Members</div>
          </div>
        </div>

        <div className="card card-hover" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            width: '46px',
            height: '46px',
            borderRadius: '10px',
            background: 'rgba(6, 182, 212, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--secondary)',
          }}>
            <Sparkles size={24} />
          </div>
          <div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800 }}>Phase 1 Active</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Multi-Tenant Foundation</div>
          </div>
        </div>

        <div className="card card-hover" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            width: '46px',
            height: '46px',
            borderRadius: '10px',
            background: 'rgba(16, 185, 129, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--success)',
          }}>
            <Activity size={24} />
          </div>
          <div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800 }}>{auditLogs.length}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Audit Logged Events</div>
          </div>
        </div>
      </div>

      {/* Main Content Grid: Team Members & Security Audit */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '1.75rem', alignItems: 'start' }}>
        {/* Team Members List */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.2rem' }}>
            <h3 style={{ fontSize: '1.15rem' }}>Team Members ({teamMembers.length})</h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Role-Based Access</span>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>User</th>
                  <th>Role</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {teamMembers.map((member) => (
                  <tr key={member.id}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{member.full_name || 'Team Member'}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{member.email}</div>
                    </td>
                    <td>
                      <span className="badge badge-primary" style={{ fontSize: '0.65rem' }}>
                        {member.roles?.[0] || 'MEMBER'}
                      </span>
                    </td>
                    <td>
                      <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>
                        Active
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Security Audit Feed */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.2rem' }}>
            <h3 style={{ fontSize: '1.15rem' }}>Security Audit Log</h3>
            <span className="badge badge-primary" style={{ fontSize: '0.65rem' }}>Immutable</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {auditLogs.length === 0 ? (
              <p style={{ fontSize: '0.85rem', color: 'var(--text-dim)', textAlign: 'center', padding: '1rem' }}>
                No recent security actions logged yet.
              </p>
            ) : (
              auditLogs.map((log) => (
                <div
                  key={log.id}
                  style={{
                    padding: '0.75rem',
                    borderRadius: '8px',
                    backgroundColor: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid var(--border-color)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)' }}>
                      {log.action}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                      Resource: {log.resource_type || 'system'} ({new Date(log.created_at).toLocaleTimeString()})
                    </div>
                  </div>
                  <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>
                    Verified
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Invite Member Modal */}
      {showInviteModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.75)',
          backdropFilter: 'blur(6px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: '1rem',
        }}>
          <div className="card" style={{ maxWidth: '440px', width: '100%', padding: '2rem' }}>
            <h3 style={{ marginBottom: '0.5rem' }}>Add Team Member</h3>
            <p style={{ fontSize: '0.85rem', marginBottom: '1.2rem' }}>
              Create an account for a recruiter or administrator in this organization.
            </p>

            {inviteError && (
              <div className="alert alert-error">
                <span>{inviteError}</span>
              </div>
            )}

            <form onSubmit={handleCreateUser}>
              <div className="form-group">
                <label className="form-label">Email Address *</label>
                <input
                  type="email"
                  className="form-input"
                  placeholder="colleague@company.com"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Initial Password *</label>
                <input
                  type="text"
                  className="form-input"
                  value={invitePassword}
                  onChange={(e) => setInvitePassword(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Workspace Role *</label>
                <select
                  className="form-select"
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                >
                  <option value="RECRUITER">Recruiter (Manage tests & candidates)</option>
                  <option value="QUESTION_MANAGER">Question Manager (Author tests)</option>
                  <option value="COMPANY_ADMIN">Company Admin (Full organization authority)</option>
                </select>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ flex: 1 }}
                  onClick={() => setShowInviteModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ flex: 1 }}
                  disabled={isInviting}
                >
                  {isInviting ? 'Adding...' : 'Add Member'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
