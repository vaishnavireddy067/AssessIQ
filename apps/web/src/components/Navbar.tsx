import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, LogOut, User, Building, LayoutDashboard, Sparkles, Phone, Laptop } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const primaryRole = user?.roles?.[0] || 'GUEST';

  return (
    <nav style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0.9rem 2.2rem',
      backgroundColor: 'rgba(7, 11, 20, 0.85)',
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      borderBottom: '1px solid var(--border-color)',
      position: 'sticky',
      top: 0,
      zIndex: 50,
    }}>
      {/* Brand Logo */}
      <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', textDecoration: 'none' }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, #6366F1 0%, #06B6D4 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#FFF',
          boxShadow: '0 0 20px rgba(99, 102, 241, 0.5)'
        }}>
          <ShieldCheck size={24} />
        </div>
        <div>
          <span style={{ fontSize: '1.35rem', fontWeight: 800, letterSpacing: '-0.03em', color: '#FFF' }}>
            Assess<span style={{ color: 'var(--primary)' }}>IQ</span>
          </span>
          <span style={{
            display: 'block',
            fontSize: '0.65rem',
            fontWeight: 700,
            textTransform: 'uppercase',
            color: 'var(--text-muted)',
            letterSpacing: '0.09em',
            marginTop: '-3px'
          }}>
            AI Assessment Suite
          </span>
        </div>
      </Link>

      {/* Navigation Links / User Menu */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
        {isAuthenticated && user ? (
          <>
            <Link to="/dashboard" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-main)', fontSize: '0.9rem', fontWeight: 600 }}>
              <LayoutDashboard size={16} color="var(--primary)" />
              Dashboard
            </Link>

            {!user.roles.includes('CANDIDATE') && (
              <>
                <Link to="/assessments" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-main)', fontSize: '0.9rem', fontWeight: 500 }}>
                  <ShieldCheck size={16} color="var(--secondary)" />
                  Assessments
                </Link>
                <Link to="/questions" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-main)', fontSize: '0.9rem', fontWeight: 500 }}>
                  <Building size={16} color="var(--accent)" />
                  MCQ Banks
                </Link>
                <Link to="/coding" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-main)', fontSize: '0.9rem', fontWeight: 500 }}>
                  <Building size={16} color="var(--primary)" />
                  Coding Sandbox
                </Link>
                <Link to="/sql" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-main)', fontSize: '0.9rem', fontWeight: 500 }}>
                  <Building size={16} color="var(--warning)" />
                  SQL Sandbox
                </Link>
                <Link to="/copilot" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#c4b5fd', fontSize: '0.9rem', fontWeight: 600 }}>
                  <span style={{ display: 'inline-flex', padding: '0.2rem', borderRadius: '4px', background: 'linear-gradient(135deg, #6366F1, #EC4899)' }}>
                    <Sparkles size={13} color="#FFF" />
                  </span>
                  AI Copilot
                </Link>
                <Link to="/analytics" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#34d399', fontSize: '0.9rem', fontWeight: 600 }}>
                  <span style={{ display: 'inline-flex', padding: '0.2rem', borderRadius: '4px', background: 'linear-gradient(135deg, #10b981, #3b82f6)' }}>
                    <Sparkles size={13} color="#FFF" />
                  </span>
                  Analytics
                </Link>
                <Link to="/company/settings" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#38BDF8', fontSize: '0.9rem', fontWeight: 600 }}>
                  <Building size={16} color="#38BDF8" />
                  Company Portal
                </Link>
              </>
            )}

            {user.roles.includes('SUPER_ADMIN') && (
              <Link to="/superadmin" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-main)', fontSize: '0.9rem', fontWeight: 500 }}>
                <Building size={16} color="var(--secondary)" />
                Platform Admin
              </Link>
            )}

            <div style={{ width: '1px', height: '20px', backgroundColor: 'var(--border-color)' }} />

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-main)' }}>
                  {user.full_name || user.email}
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '2px' }}>
                  <span className={`badge ${
                    primaryRole === 'SUPER_ADMIN' ? 'badge-danger' :
                    primaryRole === 'COMPANY_ADMIN' ? 'badge-primary' :
                    primaryRole === 'RECRUITER' ? 'badge-warning' : 'badge-success'
                  }`} style={{ fontSize: '0.65rem', padding: '0.1rem 0.45rem' }}>
                    {primaryRole}
                  </span>
                </div>
              </div>

              <button
                onClick={handleLogout}
                className="btn btn-secondary btn-sm"
                title="Logout"
                style={{ padding: '0.5rem', borderRadius: '8px' }}
              >
                <LogOut size={16} />
              </button>
            </div>
          </>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <Link to="/exam/demo-token-123" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-muted)', fontSize: '0.9rem', fontWeight: 500 }}>
              <Laptop size={15} /> Try Exam Runner
            </Link>
            <Link to="/contact" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-muted)', fontSize: '0.9rem', fontWeight: 500 }}>
              <Phone size={14} /> Contact Sales
            </Link>
            <Link to="/login" className="btn btn-secondary btn-sm">
              Sign In
            </Link>
            <Link to="/register-company" className="btn btn-primary btn-sm">
              Start Company Trial
            </Link>
          </div>
        )}
      </div>
    </nav>
  );
};
