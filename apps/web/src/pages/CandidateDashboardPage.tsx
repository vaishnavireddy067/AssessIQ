import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiRequest } from '../api/client';
import { User, FileText, CheckCircle2, ShieldCheck, Sparkles, ExternalLink } from 'lucide-react';

export const CandidateDashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [profile, setProfile] = useState<any>(null);
  const [resumeUrl, setResumeUrl] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await apiRequest('/candidates/me');
        setProfile(res);
        setResumeUrl(res.resume_url || '');
      } catch (err) {
        console.error('Failed to load candidate profile:', err);
      }
    };
    fetchProfile();
  }, []);

  const handleUpdateResume = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsUpdating(true);
    setMessage(null);
    try {
      const updated = await apiRequest('/candidates/me', {
        method: 'PUT',
        body: JSON.stringify({ resume_url: resumeUrl }),
      });
      setProfile(updated);
      setMessage('Profile and resume link updated successfully!');
    } catch (err: any) {
      setMessage(err.message || 'Failed to update resume');
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div style={{ maxWidth: '900px', margin: '2.5rem auto', padding: '0 1.5rem' }}>
      <div className="card" style={{ marginBottom: '2rem', padding: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.4rem' }}>
              <h2 style={{ fontSize: '1.75rem' }}>Candidate Portal</h2>
              <span className="badge badge-success">Global Profile</span>
            </div>
            <p style={{ fontSize: '0.9rem' }}>
              Logged in as <strong style={{ color: 'var(--text-main)' }}>{user?.email}</strong>
            </p>
          </div>

          <div style={{
            padding: '0.6rem 1rem',
            borderRadius: '10px',
            backgroundColor: 'rgba(99, 102, 241, 0.1)',
            border: '1px solid rgba(99, 102, 241, 0.25)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.85rem',
          }}>
            <ShieldCheck size={18} color="var(--primary)" />
            <span>Anti-Cheat Verified Profile</span>
          </div>
        </div>
      </div>

      {message && (
        <div className="alert alert-success">
          <CheckCircle2 size={16} />
          <span>{message}</span>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        {/* Profile Info */}
        <div className="card">
          <h3 style={{ fontSize: '1.15rem', marginBottom: '1.2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <User size={18} color="var(--secondary)" />
            Profile Details
          </h3>

          <form onSubmit={handleUpdateResume}>
            <div className="form-group">
              <label className="form-label">Email Address</label>
              <input
                type="text"
                className="form-input"
                value={user?.email || ''}
                disabled
                style={{ opacity: 0.7 }}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Resume / Portfolio Link</label>
              <input
                type="url"
                className="form-input"
                placeholder="https://github.com/username or resume URL"
                value={resumeUrl}
                onChange={(e) => setResumeUrl(e.target.value)}
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-sm"
              disabled={isUpdating}
              style={{ marginTop: '0.5rem' }}
            >
              {isUpdating ? 'Saving...' : 'Save Profile Details'}
            </button>
          </form>
        </div>

        {/* Assigned Assessments Card */}
        <div className="card">
          <h3 style={{ fontSize: '1.15rem', marginBottom: '1.2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sparkles size={18} color="var(--primary)" />
            Assessments
          </h3>

          <div style={{
            padding: '1.5rem',
            textAlign: 'center',
            backgroundColor: 'rgba(255, 255, 255, 0.02)',
            borderRadius: '10px',
            border: '1px dashed var(--border-color)',
          }}>
            <FileText size={32} color="var(--text-dim)" style={{ margin: '0 auto 0.75rem' }} />
            <div style={{ fontWeight: 600, fontSize: '0.95rem', marginBottom: '0.3rem' }}>
              No Pending Assessments
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
              When a recruiter invites you to take a technical assessment or coding challenge, it will appear here.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
