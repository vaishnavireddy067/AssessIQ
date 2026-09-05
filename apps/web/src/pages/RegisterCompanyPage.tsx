import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Building, ShieldCheck, ArrowRight, CheckCircle2 } from 'lucide-react';

export const RegisterCompanyPage: React.FC = () => {
  const { registerCompany } = useAuth();
  const navigate = useNavigate();

  const [companyName, setCompanyName] = useState('');
  const [companySlug, setCompanySlug] = useState('');
  const [adminEmail, setAdminEmail] = useState('');
  const [adminPassword, setAdminPassword] = useState('');
  const [adminFirstName, setAdminFirstName] = useState('');
  const [adminLastName, setAdminLastName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setCompanyName(val);
    // Auto-generate slug if user hasn't explicitly customized slug
    const autoSlug = val.toLowerCase().replace(/[^a-z0-9]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');
    setCompanySlug(autoSlug);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await registerCompany({
        company_name: companyName,
        company_slug: companySlug,
        admin_email: adminEmail,
        admin_password: adminPassword,
        admin_first_name: adminFirstName || undefined,
        admin_last_name: adminLastName || undefined,
      });
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Company registration failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{
      maxWidth: '560px',
      margin: '2.5rem auto',
      padding: '0 1rem',
    }}>
      <div className="card" style={{ padding: '2.2rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.8rem' }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#FFF',
            marginBottom: '1rem',
            boxShadow: '0 0 20px rgba(99, 102, 241, 0.4)'
          }}>
            <Building size={26} />
          </div>
          <h2 style={{ fontSize: '1.6rem', marginBottom: '0.4rem' }}>Set Up Your Organization</h2>
          <p style={{ fontSize: '0.9rem' }}>Create a multi-tenant workspace to run AI assessments and hire top talent</p>
        </div>

        {error && (
          <div className="alert alert-error">
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Company Name *</label>
              <input
                type="text"
                className="form-input"
                placeholder="Acme Technologies"
                value={companyName}
                onChange={handleNameChange}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Workspace URL Slug *</label>
              <div style={{ position: 'relative' }}>
                <input
                  type="text"
                  className="form-input"
                  placeholder="acme-tech"
                  value={companySlug}
                  onChange={(e) => setCompanySlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ''))}
                  required
                />
              </div>
            </div>
          </div>

          <div style={{ height: '1px', backgroundColor: 'var(--border-color)', margin: '1.2rem 0' }} />

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Admin First Name</label>
              <input
                type="text"
                className="form-input"
                placeholder="Sarah"
                value={adminFirstName}
                onChange={(e) => setAdminFirstName(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Admin Last Name</label>
              <input
                type="text"
                className="form-input"
                placeholder="Connor"
                value={adminLastName}
                onChange={(e) => setAdminLastName(e.target.value)}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Admin Work Email *</label>
            <input
              type="email"
              className="form-input"
              placeholder="sarah@acme.com"
              value={adminEmail}
              onChange={(e) => setAdminEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Secure Password (min 8 chars) *</label>
            <input
              type="password"
              className="form-input"
              placeholder="••••••••••••"
              value={adminPassword}
              onChange={(e) => setAdminPassword(e.target.value)}
              required
              minLength={8}
            />
          </div>

          <div style={{ margin: '1.2rem 0', padding: '0.8rem', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', border: '1px solid var(--border-color)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.3rem', color: 'var(--success)', fontWeight: 600 }}>
              <CheckCircle2 size={14} /> 14-Day Free Trial of Business Plan Included
            </div>
            Includes unlimited MCQ assessments, proctoring integrity checks, and custom candidate invite links.
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', padding: '0.85rem' }}
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Creating Organization...' : 'Create Company Workspace'} <ArrowRight size={16} />
          </button>
        </form>

        <div style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: '0.85rem' }}>
          Already have an account?{' '}
          <Link to="/login" style={{ fontWeight: 600 }}>
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
};
