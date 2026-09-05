import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  ShieldCheck, Sparkles, Terminal, Code2, Database, BrainCircuit, 
  CheckCircle2, ArrowRight, Activity, Users, Lock, ChevronRight,
  BarChart3, Globe, Award, Laptop, Eye, HelpCircle, Building
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'copilot' | 'code' | 'proctoring' | 'passport'>('copilot');

  return (
    <div style={{ position: 'relative', overflow: 'hidden' }}>
      {/* ── Ambient Background Glow Blobs ────────────────────────────────────── */}
      <div className="hero-glow-blob" style={{ top: '-10%', left: '20%', background: 'radial-gradient(circle, rgba(99, 102, 241, 0.25) 0%, transparent 70%)' }} />
      <div className="hero-glow-blob" style={{ top: '20%', right: '-10%', background: 'radial-gradient(circle, rgba(6, 182, 212, 0.20) 0%, transparent 70%)' }} />

      {/* ── 1. Hero Section ─────────────────────────────────────────────────── */}
      <section style={{ maxWidth: '1200px', margin: '4rem auto 5rem auto', padding: '0 1.5rem', textAlign: 'center', position: 'relative', zIndex: 1 }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.4rem 1.1rem', borderRadius: '9999px', background: 'rgba(99, 102, 241, 0.12)', border: '1px solid rgba(99, 102, 241, 0.35)', marginBottom: '1.75rem', fontSize: '0.875rem', color: '#A5B4FC', fontWeight: 600 }}>
          <Sparkles size={16} color="var(--secondary)" />
          <span>Next-Generation Technical Recruitment & Assessment Suite</span>
          <span className="badge badge-success" style={{ marginLeft: '0.4rem', fontSize: '0.65rem' }}>v3.0 Live</span>
        </div>

        <h1 style={{ fontSize: '3.5rem', fontWeight: 800, lineHeight: 1.15, marginBottom: '1.5rem', letterSpacing: '-0.04em' }}>
          Evaluate Technical Talent <br />
          <span className="gradient-text">Faster, Smarter, & Without Bias</span>
        </h1>

        <p style={{ maxWidth: '780px', margin: '0 auto 2.5rem auto', fontSize: '1.2rem', lineHeight: 1.6, color: 'var(--text-muted)' }}>
          AssessIQ combines <strong>AI Question Copilots</strong>, <strong>Polyglot Code & SQL Sandboxes</strong>, and <strong>Multi-Modal Proctoring</strong> to help modern tech organizations identify top 1% engineering talent.
        </p>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap', marginBottom: '3.5rem' }}>
          <Link to="/register-company" className="btn btn-primary btn-lg" style={{ padding: '0.9rem 2.2rem', fontSize: '1.05rem' }}>
            Start 14-Day Company Trial <ArrowRight size={18} />
          </Link>
          <Link to="/contact" className="btn btn-secondary btn-lg" style={{ padding: '0.9rem 2rem', fontSize: '1.05rem' }}>
            Book Enterprise Demo
          </Link>
          <Link to="/exam/demo-token-123" className="btn btn-secondary btn-lg" style={{ padding: '0.9rem 1.6rem', fontSize: '1.05rem', color: 'var(--secondary)', borderColor: 'rgba(6, 182, 212, 0.3)' }}>
            <Laptop size={18} /> Try Test Runner
          </Link>
        </div>

        {/* Quick Platform Metrics Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1.25rem',
          maxWidth: '960px',
          margin: '0 auto',
        }}>
          <div className="card" style={{ padding: '1.25rem' }}>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--primary)' }}>99.4%</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Cheat Detection Accuracy</div>
          </div>
          <div className="card" style={{ padding: '1.25rem' }}>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--secondary)' }}>3.5x</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Faster Time-to-Hire</div>
          </div>
          <div className="card" style={{ padding: '1.25rem' }}>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--success)' }}>10+ Languages</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Polyglot Sandbox & SQL</div>
          </div>
          <div className="card" style={{ padding: '1.25rem' }}>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent)' }}>0% Bias</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Audited Fairness Matrix</div>
          </div>
        </div>
      </section>

      {/* ── 2. Interactive Feature Sandbox Showcase ─────────────────────────── */}
      <section style={{ maxWidth: '1200px', margin: '0 auto 6rem auto', padding: '0 1.5rem', position: 'relative', zIndex: 1 }}>
        <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
          <h2 style={{ fontSize: '2.2rem', marginBottom: '0.75rem' }}>
            Explore the <span className="gradient-text-cyan">Interactive Intelligence Studio</span>
          </h2>
          <p style={{ color: 'var(--text-muted)' }}>Click through AssessIQ's core modules to see how candidate evaluation works in real-time</p>
        </div>

        {/* Tab Controls */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '0.75rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
          <button
            className={`tab-pill ${activeTab === 'copilot' ? 'tab-pill-active' : ''}`}
            onClick={() => setActiveTab('copilot')}
          >
            <BrainCircuit size={16} /> AI Assessment Copilot
          </button>
          <button
            className={`tab-pill ${activeTab === 'code' ? 'tab-pill-active' : ''}`}
            onClick={() => setActiveTab('code')}
          >
            <Code2 size={16} /> Polyglot & SQL Sandbox
          </button>
          <button
            className={`tab-pill ${activeTab === 'proctoring' ? 'tab-pill-active' : ''}`}
            onClick={() => setActiveTab('proctoring')}
          >
            <Eye size={16} /> Sensory Proctoring HUD
          </button>
          <button
            className={`tab-pill ${activeTab === 'passport' ? 'tab-pill-active' : ''}`}
            onClick={() => setActiveTab('passport')}
          >
            <Award size={16} /> Skill Passport & Bias Radar
          </button>
        </div>

        {/* Active Tab Preview Box */}
        <div className="card" style={{ padding: '2.5rem', border: '1px solid rgba(99, 102, 241, 0.3)', boxShadow: '0 20px 60px rgba(0, 0, 0, 0.6)' }}>
          {activeTab === 'copilot' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '2rem', alignItems: 'center' }}>
              <div>
                <span className="badge badge-primary" style={{ marginBottom: '1rem' }}>AI Prompt & Resume Ingestion</span>
                <h3 style={{ fontSize: '1.6rem', marginBottom: '1rem' }}>Generate Tailored Test Suites in Seconds</h3>
                <p style={{ marginBottom: '1.5rem', lineHeight: 1.6 }}>
                  Paste any job description or uploaded candidate resume. AssessIQ synthesizes customized technical MCQs, algorithmic challenges, and SQL scenarios calibrated specifically to target seniority levels.
                </p>
                <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.6rem', fontSize: '0.9rem', marginBottom: '1.75rem' }}>
                  <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <CheckCircle2 size={16} color="var(--success)" /> Dynamic Anti-Leak: Questions re-parameterized to defeat search engines
                  </li>
                  <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <CheckCircle2 size={16} color="var(--success)" /> Automated Difficulty Calibration (Junior, Mid, Senior, Principal)
                  </li>
                  <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <CheckCircle2 size={16} color="var(--success)" /> Automated Grading Keys and detailed candidate answer explanations
                  </li>
                </ul>
                <Link to="/copilot" className="btn btn-primary btn-sm">
                  Launch Copilot Studio <ChevronRight size={14} />
                </Link>
              </div>
              <div style={{
                background: 'rgba(7, 11, 20, 0.9)',
                borderRadius: '12px',
                border: '1px solid var(--border-color)',
                padding: '1.5rem',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.85rem'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', color: 'var(--text-dim)', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                  <Terminal size={14} /> AI Copilot Synthesis Stream
                </div>
                <div style={{ color: 'var(--secondary)', marginBottom: '0.5rem' }}>&gt; Analyzing Role: Senior Distributed Systems Engineer</div>
                <div style={{ color: 'var(--text-muted)', marginBottom: '0.5rem' }}>&gt; Target Skills: Raft Consensus, gRPC, Go Concurrency, High QPS Caching</div>
                <div style={{ padding: '0.75rem', background: 'rgba(99, 102, 241, 0.1)', borderRadius: '6px', borderLeft: '3px solid var(--primary)', marginTop: '0.75rem' }}>
                  <div style={{ color: '#FFF', fontWeight: 600 }}>Q1: Leader Election Under Split-Brain Partition</div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '4px' }}>Generated: 4 Options • 1 Correct • Distractors Evaluated</div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'code' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '2rem', alignItems: 'center' }}>
              <div>
                <span className="badge badge-secondary" style={{ marginBottom: '1rem' }}>Remote Sandbox Execution</span>
                <h3 style={{ fontSize: '1.6rem', marginBottom: '1rem' }}>Polyglot Code & Live SQLite Engines</h3>
                <p style={{ marginBottom: '1.5rem', lineHeight: 1.6 }}>
                  Evaluate algorithmic problem-solving with multi-language execution (Python, JavaScript, TypeScript, Java, C++, Go, Rust) and live in-memory SQL schema validations.
                </p>
                <div style={{ display: 'flex', gap: '1rem' }}>
                  <Link to="/coding" className="btn btn-secondary btn-sm">
                    Open Coding Sandbox <ChevronRight size={14} />
                  </Link>
                  <Link to="/sql" className="btn btn-secondary btn-sm">
                    Open SQL Sandbox <ChevronRight size={14} />
                  </Link>
                </div>
              </div>
              <div style={{
                background: 'rgba(7, 11, 20, 0.9)',
                borderRadius: '12px',
                border: '1px solid var(--border-color)',
                padding: '1.5rem',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.85rem'
              }}>
                <div style={{ color: '#94A3B8', marginBottom: '0.5rem' }}>// Two Sum — Optimal Hash Map Solution</div>
                <div style={{ color: '#818CF8' }}>def solve(nums, target):</div>
                <div style={{ color: '#E2E8F0', paddingLeft: '1rem' }}>seen = {}</div>
                <div style={{ color: '#E2E8F0', paddingLeft: '1rem' }}>for i, n in enumerate(nums):</div>
                <div style={{ color: '#E2E8F0', paddingLeft: '2rem' }}>if target - n in seen: return [seen[target - n], i]</div>
                <div style={{ marginTop: '1rem', padding: '0.6rem', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '6px', color: 'var(--success)' }}>
                  ✓ All 4/4 Test Cases Passed (Runtime: 24ms, Memory: 14MB)
                </div>
              </div>
            </div>
          )}

          {activeTab === 'proctoring' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '2rem', alignItems: 'center' }}>
              <div>
                <span className="badge badge-danger" style={{ marginBottom: '1rem' }}>Anti-Cheat & Integrity Studio</span>
                <h3 style={{ fontSize: '1.6rem', marginBottom: '1rem' }}>Real-Time Multi-Modal Proctoring</h3>
                <p style={{ marginBottom: '1.5rem', lineHeight: 1.6 }}>
                  Defend assessment integrity with audio classification, browser tab-focus tracking, multi-face detection, and AI copy-paste interception.
                </p>
                <Link to="/exam/demo-token-123" className="btn btn-primary btn-sm">
                  Test Live Exam Runner <ChevronRight size={14} />
                </Link>
              </div>
              <div style={{
                background: 'rgba(7, 11, 20, 0.9)',
                borderRadius: '12px',
                border: '1px solid var(--border-color)',
                padding: '1.5rem',
                fontSize: '0.85rem'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <span style={{ fontWeight: 600 }}>Proctoring Telemetry HUD</span>
                  <span className="badge badge-success">Integrity: 98%</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                    <span>Face Recognition</span>
                    <span style={{ color: 'var(--success)' }}>1 Present (Centered)</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                    <span>Audio Classification</span>
                    <span style={{ color: 'var(--success)' }}>Normal Environment</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                    <span>Tab Switch Events</span>
                    <span style={{ color: 'var(--text-muted)' }}>0 Detected</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'passport' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '2rem', alignItems: 'center' }}>
              <div>
                <span className="badge badge-accent" style={{ marginBottom: '1rem' }}>Verifiable Credentials</span>
                <h3 style={{ fontSize: '1.6rem', marginBottom: '1rem' }}>Skill Passports & Algorithmic Fairness</h3>
                <p style={{ marginBottom: '1.5rem', lineHeight: 1.6 }}>
                  Eliminate hiring bias with standardized competency scorecards and continuous adverse impact monitoring across demographic bands.
                </p>
                <Link to="/analytics" className="btn btn-secondary btn-sm">
                  View Analytics Studio <ChevronRight size={14} />
                </Link>
              </div>
              <div style={{
                background: 'rgba(7, 11, 20, 0.9)',
                borderRadius: '12px',
                border: '1px solid var(--border-color)',
                padding: '1.5rem',
              }}>
                <div style={{ fontWeight: 700, fontSize: '1rem', marginBottom: '0.5rem' }}>Jane Developer — Verified Passport</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '1rem' }}>Credential Hash: #PASS-8849-B2</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '2px' }}>
                      <span>Backend Architecture</span>
                      <span style={{ color: 'var(--primary)', fontWeight: 600 }}>94th Percentile</span>
                    </div>
                    <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px' }}>
                      <div style={{ width: '94%', height: '100%', background: 'var(--primary)', borderRadius: '3px' }} />
                    </div>
                  </div>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '2px' }}>
                      <span>Concurrency & Memory</span>
                      <span style={{ color: 'var(--secondary)', fontWeight: 600 }}>88th Percentile</span>
                    </div>
                    <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px' }}>
                      <div style={{ width: '88%', height: '100%', background: 'var(--secondary)', borderRadius: '3px' }} />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* ── 3. Why AssessIQ: Comparison Matrix ───────────────────────────────── */}
      <section style={{ maxWidth: '1200px', margin: '0 auto 6rem auto', padding: '0 1.5rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <h2 style={{ fontSize: '2.2rem', marginBottom: '0.75rem' }}>
            Why Leading Engineering Teams Choose <span className="gradient-text">AssessIQ</span>
          </h2>
          <p style={{ color: 'var(--text-muted)' }}>How AssessIQ compares to legacy assessment platforms</p>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th style={{ width: '35%' }}>Feature Capability</th>
                <th style={{ width: '25%', color: 'var(--primary)' }}>AssessIQ (Next-Gen)</th>
                <th style={{ width: '20%' }}>HackerRank / Codility</th>
                <th style={{ width: '20%' }}>TestGorilla / Mettl</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ fontWeight: 600 }}>AI Question Synthesis from Job Descriptions</td>
                <td><span className="badge badge-success">Native Real-Time</span></td>
                <td><span className="badge badge-danger">Limited / Static</span></td>
                <td><span className="badge badge-danger">Not Available</span></td>
              </tr>
              <tr>
                <td style={{ fontWeight: 600 }}>Multi-Modal Audio & Visual Sensory Proctoring</td>
                <td><span className="badge badge-success">Included Full Suite</span></td>
                <td><span className="badge badge-warning">Basic Snapshots</span></td>
                <td><span className="badge badge-warning">Third-party Addon</span></td>
              </tr>
              <tr>
                <td style={{ fontWeight: 600 }}>Automated Question Leak Radar</td>
                <td><span className="badge badge-success">Automated Continuous</span></td>
                <td><span className="badge badge-danger">Manual / Stale</span></td>
                <td><span className="badge badge-danger">Manual</span></td>
              </tr>
              <tr>
                <td style={{ fontWeight: 600 }}>Algorithmic Bias & EEOC 4/5ths Rule Audits</td>
                <td><span className="badge badge-success">Integrated Dashboard</span></td>
                <td><span className="badge badge-danger">No</span></td>
                <td><span className="badge badge-danger">No</span></td>
              </tr>
              <tr>
                <td style={{ fontWeight: 600 }}>Self-Serve Multi-Tenant Organization Setup</td>
                <td><span className="badge badge-success">Instant 14-Day Trial</span></td>
                <td><span className="badge badge-warning">Sales Call Gate</span></td>
                <td><span className="badge badge-warning">Tier Restricted</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* ── 4. Pricing & Plans ──────────────────────────────────────────────── */}
      <section style={{ maxWidth: '1200px', margin: '0 auto 6rem auto', padding: '0 1.5rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <h2 style={{ fontSize: '2.2rem', marginBottom: '0.75rem' }}>Transparent SaaS Pricing</h2>
          <p style={{ color: 'var(--text-muted)' }}>Scale your assessment pipeline with zero hidden fees</p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
          {/* Starter Plan */}
          <div className="card card-hover" style={{ padding: '2.2rem' }}>
            <div style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.5rem' }}>Starter</div>
            <p style={{ fontSize: '0.85rem', marginBottom: '1.5rem' }}>For growing startups hiring their core engineering teams.</p>
            <div style={{ fontSize: '2.5rem', fontWeight: 800, marginBottom: '1.5rem' }}>
              $149 <span style={{ fontSize: '1rem', fontWeight: 400, color: 'var(--text-muted)' }}>/ month</span>
            </div>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.875rem', marginBottom: '2rem' }}>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><CheckCircle2 size={16} color="var(--success)" /> Up to 50 Candidates / month</li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><CheckCircle2 size={16} color="var(--success)" /> Standard Coding & SQL Sandbox</li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><CheckCircle2 size={16} color="var(--success)" /> AI Question Copilot (50 generations)</li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><CheckCircle2 size={16} color="var(--success)" /> Basic Proctoring & Tab Tracking</li>
            </ul>
            <Link to="/register-company" className="btn btn-secondary" style={{ width: '100%' }}>
              Start Free Trial
            </Link>
          </div>

          {/* Business / Growth Plan */}
          <div className="card card-hover" style={{ padding: '2.2rem', borderColor: 'var(--primary)', boxShadow: '0 0 35px rgba(99, 102, 241, 0.25)', position: 'relative' }}>
            <div style={{ position: 'absolute', top: '-12px', right: '20px' }}>
              <span className="badge badge-primary" style={{ background: 'var(--primary)', color: '#FFF' }}>Most Popular</span>
            </div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.5rem' }}>Business</div>
            <p style={{ fontSize: '0.85rem', marginBottom: '1.5rem' }}>For scale-ups and high-volume recruitment agencies.</p>
            <div style={{ fontSize: '2.5rem', fontWeight: 800, marginBottom: '1.5rem' }}>
              $399 <span style={{ fontSize: '1rem', fontWeight: 400, color: 'var(--text-muted)' }}>/ month</span>
            </div>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.875rem', marginBottom: '2rem' }}>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><CheckCircle2 size={16} color="var(--success)" /> Unlimited Candidate Assessments</li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><CheckCircle2 size={16} color="var(--success)" /> Full Audio/Visual Sensory Proctoring</li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><CheckCircle2 size={16} color="var(--success)" /> Unlimited AI Copilot & Resumes</li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><CheckCircle2 size={16} color="var(--success)" /> Candidate Skill Passports & Leak Radar</li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><CheckCircle2 size={16} color="var(--success)" /> ATS Webhooks (Workable, Greenhouse)</li>
            </ul>
            <Link to="/register-company" className="btn btn-primary" style={{ width: '100%' }}>
              Start 14-Day Free Trial
            </Link>
          </div>

          {/* Enterprise Custom */}
          <div className="card card-hover" style={{ padding: '2.2rem' }}>
            <div style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.5rem' }}>Enterprise</div>
            <p style={{ fontSize: '0.85rem', marginBottom: '1.5rem' }}>For large enterprises needing custom compliance & dedicated SLAs.</p>
            <div style={{ fontSize: '2.5rem', fontWeight: 800, marginBottom: '1.5rem' }}>
              Custom
            </div>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.875rem', marginBottom: '2rem' }}>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><CheckCircle2 size={16} color="var(--success)" /> Custom Question Ingestion & Migration</li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><CheckCircle2 size={16} color="var(--success)" /> SAML 2.0 / Okta SSO Integration</li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><CheckCircle2 size={16} color="var(--success)" /> 99.99% Dedicated Uptime SLA</li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><CheckCircle2 size={16} color="var(--success)" /> Dedicated Account Architect</li>
            </ul>
            <Link to="/contact" className="btn btn-secondary" style={{ width: '100%' }}>
              Contact Enterprise Sales
            </Link>
          </div>
        </div>
      </section>

      {/* ── 5. Call to Action Banner ────────────────────────────────────────── */}
      <section style={{ maxWidth: '1200px', margin: '0 auto 6rem auto', padding: '0 1.5rem' }}>
        <div className="card" style={{
          padding: '4rem 2rem',
          textAlign: 'center',
          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(6, 182, 212, 0.15) 100%)',
          border: '1px solid rgba(99, 102, 241, 0.4)',
        }}>
          <h2 style={{ fontSize: '2.4rem', marginBottom: '1rem' }}>
            Ready to Build an Elite Engineering Team?
          </h2>
          <p style={{ maxWidth: '600px', margin: '0 auto 2rem auto', fontSize: '1.1rem', color: 'var(--text-muted)' }}>
            Join forward-thinking engineering organizations hiring top developers with AssessIQ today.
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <Link to="/register-company" className="btn btn-primary btn-lg">
              Create Organization Account <ArrowRight size={18} />
            </Link>
            <Link to="/contact" className="btn btn-secondary btn-lg">
              Contact Sales & Support
            </Link>
          </div>
        </div>
      </section>

      {/* ── 6. Footer ───────────────────────────────────────────────────────── */}
      <footer style={{
        borderTop: '1px solid var(--border-color)',
        padding: '3.5rem 1.5rem 2.5rem 1.5rem',
        background: 'rgba(7, 11, 20, 0.95)',
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '2.5rem',
          marginBottom: '3rem',
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1rem' }}>
              <div style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #6366F1 0%, #06B6D4 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#FFF',
              }}>
                <ShieldCheck size={20} />
              </div>
              <span style={{ fontSize: '1.2rem', fontWeight: 800 }}>Assess<span style={{ color: 'var(--primary)' }}>IQ</span></span>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-dim)', lineHeight: 1.6 }}>
              The enterprise technical assessment & AI integrity engine for modern engineering teams.
            </p>
          </div>

          <div>
            <div style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: '1rem' }}>Product</div>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.85rem' }}>
              <li><Link to="/exam/demo-token-123">Interactive Exam Runner</Link></li>
              <li><Link to="/login">Recruiter Dashboard</Link></li>
              <li><Link to="/register-company">Organization Trial</Link></li>
            </ul>
          </div>

          <div>
            <div style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: '1rem' }}>Developers & API</div>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.85rem' }}>
              <li><a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">OpenAPI / Swagger</a></li>
              <li><a href="http://localhost:8000/redoc" target="_blank" rel="noreferrer">ReDoc API Reference</a></li>
              <li><Link to="/analytics">Fairness & Bias Radar</Link></li>
            </ul>
          </div>

          <div>
            <div style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: '1rem' }}>Company & Contact</div>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.85rem' }}>
              <li><Link to="/contact">Contact Sales & Support</Link></li>
              <li><Link to="/login">Sign In</Link></li>
              <li><Link to="/register-candidate">Candidate Portal</Link></li>
            </ul>
          </div>
        </div>

        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          fontSize: '0.8rem',
          color: 'var(--text-dim)',
          borderTop: '1px solid rgba(255,255,255,0.05)',
          paddingTop: '1.5rem',
        }}>
          <div>© {new Date().getFullYear()} AssessIQ Inc. All rights reserved.</div>
          <div style={{ display: 'flex', gap: '1.5rem' }}>
            <span>SOC2 Type II Certified</span>
            <span>GDPR Compliant</span>
            <span>99.9% Uptime SLA</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
