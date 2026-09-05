import React, { useEffect, useState } from 'react';
import { apiRequest } from '../api/client';
import { 
  Building, Users, Activity, ShieldCheck, Database, 
  Layers, CreditCard, AlertTriangle, CheckCircle2, TrendingUp 
} from 'lucide-react';

export const SuperAdminPage: React.FC = () => {
  const [metrics, setMetrics] = useState<any>(null);
  const [tenants, setTenants] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [updatingCompanyId, setUpdatingCompanyId] = useState<string | null>(null);

  const loadAdminData = async () => {
    try {
      setIsLoading(true);
      const [mRes, tRes] = await Promise.all([
        apiRequest('/admin/platform/metrics'),
        apiRequest('/admin/tenants'),
      ]);
      setMetrics(mRes);
      setTenants(tRes);
    } catch (err) {
      console.error('Failed to fetch admin stats:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAdminData();
  }, []);

  const handleChangePlan = async (companyId: string, newPlan: string) => {
    try {
      setUpdatingCompanyId(companyId);
      await apiRequest(`/admin/tenants/${companyId}/plan`, {
        method: 'POST',
        body: JSON.stringify({ plan_code: newPlan }),
      });
      await loadAdminData();
    } catch (err) {
      alert('Failed to update subscription tier');
    } finally {
      setUpdatingCompanyId(null);
    }
  };

  if (isLoading) {
    return (
      <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        Loading platform administration & observability telemetry...
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '2rem auto', padding: '0 1.5rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.4rem' }}>
          <h1 style={{ fontSize: '1.85rem' }}>SuperAdmin SaaS Platform Console</h1>
          <span className="badge badge-danger">SUPER_ADMIN ONLY</span>
        </div>
        <p style={{ fontSize: '0.95rem', color: 'var(--text-muted)' }}>
          Multi-tenant orchestration, global telemetry, subscription tiering, and security audits
        </p>
      </div>

      {/* Telemetry Metric Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '1.25rem',
        marginBottom: '2.5rem',
      }}>
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', color: 'var(--primary)', marginBottom: '0.4rem' }}>
            <Building size={18} />
            <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Total Companies</span>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800 }}>{metrics?.tenants?.total_companies || 0}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
            {metrics?.tenants?.total_users || 0} users across all tenants
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', color: 'var(--success)', marginBottom: '0.4rem' }}>
            <Activity size={18} />
            <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Candidate Attempts</span>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800 }}>{metrics?.assessments?.total_candidate_attempts || 0}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
            Across {metrics?.assessments?.total_published_assessments || 0} published assessments
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', color: '#f87171', marginBottom: '0.4rem' }}>
            <ShieldCheck size={18} />
            <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Proctoring Flags</span>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#f87171' }}>
            {metrics?.assessments?.flagged_proctoring_attempts || 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
            Incident Rate: {metrics?.assessments?.incident_rate_percentage || 0}%
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', color: '#c4b5fd', marginBottom: '0.4rem' }}>
            <Database size={18} />
            <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Audit Logs</span>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800 }}>{metrics?.system_health?.audit_trail_depth || 0}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
            Immutable security event depth
          </div>
        </div>
      </div>

      {/* Global Tenant Management Table */}
      <div className="card" style={{ marginBottom: '2.5rem' }}>
        <h3 style={{ fontSize: '1.25rem', marginBottom: '1.2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <CreditCard size={20} color="var(--primary)" /> Tenant Subscription & Resource Management
        </h3>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Company Name</th>
                <th>Slug</th>
                <th>Users</th>
                <th>Assessments</th>
                <th>Plan Tier</th>
                <th>Candidate Usage</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {tenants.map((t) => (
                <tr key={t.id}>
                  <td style={{ fontWeight: 600 }}>{t.name}</td>
                  <td style={{ color: 'var(--text-muted)', fontFamily: 'monospace', fontSize: '0.8rem' }}>{t.slug}</td>
                  <td>{t.user_count}</td>
                  <td>{t.assessment_count}</td>
                  <td>
                    <span className={`badge ${
                      t.plan_code === 'ENTERPRISE' ? 'badge-primary' :
                      t.plan_code === 'BUSINESS' ? 'badge-success' : 'badge-secondary'
                    }`}>
                      {t.plan_name}
                    </span>
                  </td>
                  <td>
                    <span style={{ fontSize: '0.85rem' }}>
                      {t.monthly_candidates_used} / {t.monthly_candidate_limit}
                    </span>
                  </td>
                  <td>
                    <select
                      className="form-input"
                      value={t.plan_code}
                      disabled={updatingCompanyId === t.id}
                      onChange={(e) => handleChangePlan(t.id, e.target.value)}
                      style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                    >
                      <option value="STARTER">Starter ($49/mo)</option>
                      <option value="BUSINESS">Business ($199/mo)</option>
                      <option value="ENTERPRISE">Enterprise ($799/mo)</option>
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
