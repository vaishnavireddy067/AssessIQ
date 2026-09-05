import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, ArrowRight, Sparkles, Building, CheckCircle2, Lock, KeyRound } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const fillDemo = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
  };

  return (
    <div style={{
      maxWidth: '960px',
      margin: '3rem auto',
      padding: '0 1.5rem',
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
      gap: '2rem',
      alignItems: 'center',
    }}>
      {/* Left Pitch / Feature Summary */}
      <div style={{ padding: '1rem' }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.4rem',
          padding: '0.3rem 0.8rem',
          borderRadius: '9999px',
          background: 'rgba(99, 102, 241, 0.12)',
          border: '1px solid rgba(99, 102, 241, 0.3)',
          color: '#A5B4FC',
          fontSize: '0.8rem',
          fontWeight: 600,
          marginBottom: '1.25rem'
        }}>
          <Sparkles size={14} color="var(--secondary)" /> Secure Enterprise Portal
        </div>
        <h1 style={{ fontSize: '2.4rem', marginBottom: '1rem', lineHeight: 1.2 }}>
          Sign in to your <span className="gradient-text">AssessIQ Workspace</span>
        </h1>
        <p style={{ fontSize: '1.05rem', color: 'var(--text-muted)', lineHeight: 1.6, marginBottom: '2rem' }}>
          Evaluate engineering candidates with multi-modal AI proctoring, polyglot coding sandboxes, and automated leak radar.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--success)' }}>
              <CheckCircle2 size={18} />
            </div>
            <div style={{ fontSize: '0.9rem', color: '#E2E8F0' }}>Multi-Tenant Role-Based Access Control</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(6, 182, 212, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--secondary)' }}>
              <CheckCircle2 size={18} />
            </div>
            <div style={{ fontSize: '0.9rem', color: '#E2E8F0' }}>Deterministic Anti-Cheat & Audio Telemetry</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary)' }}>
              <CheckCircle2 size={18} />
            </div>
            <div style={{ fontSize: '0.9rem', color: '#E2E8F0' }}>Continuous Question Leak Radar & Bias Auditing</div>
          </div>
        </div>
      </div>

      {/* Right Login Card */}
      <div className="card" style={{ padding: '2.5rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #6366F1 0%, #06B6D4 100%)',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#FFF',
            marginBottom: '1rem',
            boxShadow: '0 0 25px rgba(99, 102, 241, 0.4)'
          }}>
            <ShieldCheck size={28} />
          </div>
          <h2 style={{ fontSize: '1.6rem', marginBottom: '0.35rem' }}>Welcome Back</h2>
          <p style={{ fontSize: '0.9rem' }}>Enter your credentials to access your assessment console</p>
        </div>

        {error && (
          <div className="alert alert-error">
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Work Email</label>
            <input
              type="email"
              className="form-input"
              placeholder="name@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password"
              className="form-input"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '0.75rem', padding: '0.85rem' }}
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Authenticating...' : 'Sign In'} <ArrowRight size={16} />
          </button>
        </form>

        {/* Demo Quick Fill Helper */}
        <div style={{
          marginTop: '1.75rem',
          paddingTop: '1.25rem',
          borderTop: '1px solid var(--border-color)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
            <Sparkles size={14} color="var(--secondary)" />
            <span>One-Click Seed Accounts:</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => fillDemo('admin@acme.com', 'AcmeAdmin2026!')}
              style={{ fontSize: '0.75rem', justifyContent: 'flex-start' }}
            >
              🏢 Company Admin
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => fillDemo('recruiter@acme.com', 'AcmeRecruiter2026!')}
              style={{ fontSize: '0.75rem', justifyContent: 'flex-start' }}
            >
              🎯 Recruiter
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => fillDemo('superadmin@assessiq.com', 'AssessIQ2026!Super')}
              style={{ fontSize: '0.75rem', justifyContent: 'flex-start' }}
            >
              ⚡ Super Admin
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => fillDemo('candidate@example.com', 'Candidate2026!')}
              style={{ fontSize: '0.75rem', justifyContent: 'flex-start' }}
            >
              👤 Candidate
            </button>
          </div>
        </div>

        {/* Footer Links */}
        <div style={{
          marginTop: '1.5rem',
          textAlign: 'center',
          fontSize: '0.85rem',
          color: 'var(--text-muted)',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.5rem'
        }}>
          <div>
            Need to assess candidates?{' '}
            <Link to="/register-company" style={{ fontWeight: 600 }}>
              Create Company Account
            </Link>
          </div>
          <div>
            Taking a test?{' '}
            <Link to="/register-candidate" style={{ color: 'var(--secondary)' }}>
              Candidate Sign Up
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
