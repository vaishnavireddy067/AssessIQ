import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { apiRequest } from '../api/client';
import { 
  Building2, Mail, Phone, Clock, ShieldCheck, CheckCircle2, 
  ArrowRight, Sparkles, Send, MessageSquare, Headphones, Award
} from 'lucide-react';

export const ContactPage: React.FC = () => {
  const [name, setName] = useState('');
  const [workEmail, setWorkEmail] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [companySize, setCompanySize] = useState('50-200');
  const [inquiryType, setInquiryType] = useState('enterprise_demo');
  const [phone, setPhone] = useState('');
  const [message, setMessage] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submittedTicket, setSubmittedTicket] = useState<{
    ticket_id: string;
    message: string;
    received_at: string;
  } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const res = await apiRequest<{
        ticket_id: string;
        message: string;
        received_at: string;
      }>('/contact', {
        method: 'POST',
        body: JSON.stringify({
          name,
          work_email: workEmail,
          company_name: companyName,
          company_size: companySize,
          inquiry_type: inquiryType,
          phone: phone || undefined,
          message,
        }),
      });
      setSubmittedTicket(res);
    } catch (err: any) {
      setError(err.message || 'Failed to submit inquiry. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '2rem auto', padding: '0 1.5rem' }}>
      {/* Header Banner */}
      <div style={{ textAlign: 'center', marginBottom: '3.5rem', position: 'relative' }}>
        <div className="badge badge-primary" style={{ marginBottom: '1rem', padding: '0.4rem 1rem' }}>
          <Sparkles size={14} /> Enterprise Sales & Support
        </div>
        <h1 style={{ fontSize: '2.8rem', marginBottom: '1rem' }}>
          Let's Elevate Your <span className="gradient-text">Hiring Pipeline</span>
        </h1>
        <p style={{ maxWidth: '650px', margin: '0 auto', fontSize: '1.1rem', color: 'var(--text-muted)' }}>
          Whether you need a custom enterprise pilot, volume assessment pricing, or dedicated ATS integrations, our recruitment engineering team is here to help.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 0.9fr', gap: '2.5rem', alignItems: 'start' }}>
        {/* Left Form Card */}
        <div className="card" style={{ padding: '2.5rem' }}>
          {submittedTicket ? (
            <div style={{ textAlign: 'center', padding: '2rem 1rem' }}>
              <div style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                background: 'rgba(16, 185, 129, 0.15)',
                color: 'var(--success)',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1.5rem',
                border: '1px solid rgba(16, 185, 129, 0.3)',
              }}>
                <CheckCircle2 size={36} />
              </div>
              <h2 style={{ fontSize: '1.8rem', marginBottom: '0.75rem' }}>Inquiry Received!</h2>
              <p style={{ fontSize: '1rem', marginBottom: '1.5rem', color: 'var(--text-muted)' }}>
                {submittedTicket.message}
              </p>
              <div style={{
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid var(--border-color)',
                borderRadius: '12px',
                padding: '1.25rem',
                marginBottom: '2rem',
                display: 'inline-block',
                textAlign: 'left',
              }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Reference Ticket ID
                </div>
                <div style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--secondary)', fontFamily: 'var(--font-mono)' }}>
                  {submittedTicket.ticket_id}
                </div>
              </div>
              <div>
                <button
                  className="btn btn-secondary"
                  onClick={() => {
                    setSubmittedTicket(null);
                    setMessage('');
                  }}
                >
                  Submit Another Inquiry
                </button>
              </div>
            </div>
          ) : (
            <>
              <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>Request Demo or Contact Us</h2>
              <p style={{ fontSize: '0.9rem', marginBottom: '1.75rem' }}>
                Fill in the details below and we will connect you with a solutions architect.
              </p>

              {error && (
                <div className="alert alert-error">
                  <span>{error}</span>
                </div>
              )}

              <form onSubmit={handleSubmit}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div className="form-group">
                    <label className="form-label">Full Name *</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="Alex Mercer"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Work Email *</label>
                    <input
                      type="email"
                      className="form-input"
                      placeholder="alex@company.com"
                      value={workEmail}
                      onChange={(e) => setWorkEmail(e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '1rem' }}>
                  <div className="form-group">
                    <label className="form-label">Company Name *</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="Acme Technologies"
                      value={companyName}
                      onChange={(e) => setCompanyName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Company Size</label>
                    <select
                      className="form-select"
                      value={companySize}
                      onChange={(e) => setCompanySize(e.target.value)}
                    >
                      <option value="1-10">1 - 10 employees</option>
                      <option value="10-50">10 - 50 employees</option>
                      <option value="50-200">50 - 200 employees</option>
                      <option value="200-1000">200 - 1,000 employees</option>
                      <option value="1000+">1,000+ Enterprise</option>
                    </select>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div className="form-group">
                    <label className="form-label">Inquiry Purpose *</label>
                    <select
                      className="form-select"
                      value={inquiryType}
                      onChange={(e) => setInquiryType(e.target.value)}
                    >
                      <option value="enterprise_demo">🎯 Request Live Product Demo</option>
                      <option value="sales_pricing">💼 Custom Enterprise Pricing</option>
                      <option value="ats_integration">🔗 ATS Integrations (Workable, Greenhouse)</option>
                      <option value="custom_bank">📚 Custom Question Bank Migration</option>
                      <option value="support">🛠 Technical Customer Support</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Phone Number (Optional)</label>
                    <input
                      type="tel"
                      className="form-input"
                      placeholder="+1 (555) 019-2834"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">How can we help your team? *</label>
                  <textarea
                    className="form-textarea"
                    rows={4}
                    placeholder="Tell us about your assessment volume, technical roles, or specific proctoring requirements..."
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    required
                  />
                </div>

                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ width: '100%', padding: '0.9rem', marginTop: '0.5rem' }}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Sending Request...' : 'Send Inquiry & Book Demo'} <Send size={16} />
                </button>
              </form>
            </>
          )}
        </div>

        {/* Right Info Cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Direct Channels */}
          <div className="card" style={{ padding: '2rem' }}>
            <h3 style={{ fontSize: '1.25rem', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Headphones size={20} color="var(--primary)" /> Direct Channels
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
                <div style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '10px',
                  background: 'rgba(99, 102, 241, 0.15)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--primary)',
                }}>
                  <Mail size={18} />
                </div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>Enterprise Sales</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>sales@assessiq.io</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '2px' }}>Guaranteed response within 2 hours</div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
                <div style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '10px',
                  background: 'rgba(6, 182, 212, 0.15)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--secondary)',
                }}>
                  <Phone size={18} />
                </div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>Direct Line</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>+1 (800) 555-IQ-ASSESS</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '2px' }}>Mon - Fri, 9am - 8pm EST</div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
                <div style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '10px',
                  background: 'rgba(16, 185, 129, 0.15)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--success)',
                }}>
                  <Clock size={18} />
                </div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>99.9% SLA & Support</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>support@assessiq.io</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '2px' }}>24/7 dedicated proctoring coverage</div>
                </div>
              </div>
            </div>
          </div>

          {/* Trust & Guarantees */}
          <div className="card" style={{ padding: '2rem', background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(6, 182, 212, 0.05) 100%)' }}>
            <h3 style={{ fontSize: '1.15rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Award size={20} color="var(--secondary)" /> Why Companies Choose AssessIQ
            </h3>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.875rem' }}>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}>
                <CheckCircle2 size={16} color="var(--success)" /> SOC2 Type II & GDPR Compliant Data Pipeline
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}>
                <CheckCircle2 size={16} color="var(--success)" /> Custom Question Ingestion from Existing PDFs/Docs
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}>
                <CheckCircle2 size={16} color="var(--success)" /> Automated Candidate Leak Radar & Anti-Cheat Audio/Visual
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}>
                <CheckCircle2 size={16} color="var(--success)" /> Multi-tenant White-labeling for Enterprise Brands
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
