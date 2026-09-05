import React, { useState } from 'react';
import { apiRequest } from '../api/client';
import { FileText, Sparkles, Loader2, CheckCircle2, AlertCircle, Briefcase, Award } from 'lucide-react';

interface ResumeAnalysisModalProps {
  onClose: () => void;
}

export const ResumeAnalysisModal: React.FC<ResumeAnalysisModalProps> = ({ onClose }) => {
  const [candidateName, setCandidateName] = useState('');
  const [candidateEmail, setCandidateEmail] = useState('');
  const [resumeText, setResumeText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const sampleResume = `Alex Mercer
alex.mercer@example.com
Full-Stack Software Engineer with 4 years of experience building high-scale cloud platforms.

TECHNICAL SKILLS:
- Languages & Frameworks: Python, FastAPI, TypeScript, React, Node.js, SQL
- Infrastructure: Docker, Kubernetes, AWS, PostgreSQL, Redis, CI/CD pipelines
- Principles: Microservices architecture, REST APIs, Distributed caching

WORK EXPERIENCE:
Senior Software Engineer - CloudScale Inc (2022 - Present)
- Designed and maintained Python FastAPI microservices handling 50M+ requests monthly.
- Architected PostgreSQL database schemas with read-replicas and connection pooling.
- Containerized development and staging environments using Docker and Kubernetes.

EDUCATION:
Bachelor of Science in Computer Science, State University (2018 - 2022)`;

  const handleAnalyze = async () => {
    if (!resumeText.trim()) return;
    setIsAnalyzing(true);
    setError(null);

    try {
      const res = await apiRequest('/ai/resume/analyze', {
        method: 'POST',
        body: JSON.stringify({
          candidate_name: candidateName || 'Candidate',
          candidate_email: candidateEmail || 'candidate@example.com',
          resume_text: resumeText,
        }),
      });
      setAnalysisResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to analyze resume');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.8)', backdropFilter: 'blur(8px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '1rem',
    }}>
      <div className="card" style={{ maxWidth: '780px', width: '100%', maxHeight: '92vh', overflowY: 'auto', padding: '2rem' }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <div style={{
              width: '38px', height: '38px', borderRadius: '10px',
              background: 'linear-gradient(135deg, #3B82F6, #8B5CF6)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 0 20px rgba(59, 130, 246, 0.4)',
            }}>
              <FileText size={20} color="#FFF" />
            </div>
            <div>
              <h3 style={{ fontSize: '1.2rem', margin: 0 }}>Candidate Resume Intelligence</h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', margin: 0 }}>
                AI-driven skill extraction & advisory test path recommendations
              </p>
            </div>
          </div>
          <button onClick={onClose} className="btn btn-secondary btn-sm">Close</button>
        </div>

        {/* Input Form */}
        {!analysisResult ? (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.4rem', display: 'block' }}>
                  Candidate Full Name
                </label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Alex Mercer"
                  value={candidateName}
                  onChange={(e) => setCandidateName(e.target.value)}
                  style={{ width: '100%' }}
                />
              </div>
              <div>
                <label style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.4rem', display: 'block' }}>
                  Candidate Email
                </label>
                <input
                  type="email"
                  className="form-input"
                  placeholder="e.g. alex@example.com"
                  value={candidateEmail}
                  onChange={(e) => setCandidateEmail(e.target.value)}
                  style={{ width: '100%' }}
                />
              </div>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                <label style={{ fontSize: '0.85rem', fontWeight: 600 }}>
                  Resume Plain Text / CV Content
                </label>
                <button
                  type="button"
                  onClick={() => {
                    setResumeText(sampleResume);
                    setCandidateName('Alex Mercer');
                    setCandidateEmail('alex.mercer@example.com');
                  }}
                  className="btn btn-secondary btn-sm"
                  style={{ fontSize: '0.7rem', padding: '0.2rem 0.6rem' }}
                >
                  Load Sample Resume
                </button>
              </div>
              <textarea
                className="form-input"
                rows={9}
                placeholder="Paste candidate resume content, education, skills, and work history here..."
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                style={{ width: '100%', fontFamily: 'monospace', fontSize: '0.85rem', lineHeight: '1.4' }}
              />
            </div>

            {error && (
              <div className="alert alert-error" style={{ marginBottom: '1rem', fontSize: '0.85rem' }}>
                <AlertCircle size={14} /> {error}
              </div>
            )}

            <button
              onClick={handleAnalyze}
              className="btn btn-primary"
              disabled={isAnalyzing || !resumeText.trim()}
              style={{ width: '100%', padding: '0.85rem', fontSize: '1rem' }}
            >
              {isAnalyzing ? (
                <><Loader2 size={18} className="spin" /> Analyzing Resume & Extracting Skills...</>
              ) : (
                <><Sparkles size={18} /> Run AI Resume Analysis</>
              )}
            </button>
          </div>
        ) : (
          /* Analysis Results View */
          <div>
            {/* Advisory Banner */}
            <div style={{
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              marginBottom: '1.5rem',
              fontSize: '0.8rem',
              color: '#93c5fd',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}>
              <AlertCircle size={16} />
              <span>
                <strong>Advisory Only:</strong> This AI analysis provides hiring recommendations to assist recruiters. It does not auto-reject or make unilateral employment decisions.
              </span>
            </div>

            {/* Profile Overview Card */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '1rem',
              marginBottom: '1.5rem',
            }}>
              <div style={{ padding: '0.9rem', borderRadius: '8px', backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Estimated Experience</div>
                <div style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--primary)' }}>
                  {analysisResult.years_experience} Years
                </div>
              </div>
              <div style={{ padding: '0.9rem', borderRadius: '8px', backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Education</div>
                <div style={{ fontSize: '1.05rem', fontWeight: 700 }}>
                  {analysisResult.education_level}
                </div>
              </div>
              <div style={{ padding: '0.9rem', borderRadius: '8px', backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Domains</div>
                <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap', marginTop: '0.2rem' }}>
                  {analysisResult.domain_tags.map((tag: string, i: number) => (
                    <span key={i} className="badge badge-secondary" style={{ fontSize: '0.65rem' }}>{tag}</span>
                  ))}
                </div>
              </div>
            </div>

            {/* Extracted Skills */}
            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ fontSize: '0.95rem', marginBottom: '0.6rem' }}>Extracted Technical Competencies</h4>
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                {analysisResult.extracted_skills.map((skill: string, i: number) => (
                  <span key={i} className="badge badge-primary" style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}>
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            {/* Recommended Assessments */}
            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ fontSize: '0.95rem', marginBottom: '0.6rem' }}>Recommended Assessment Modules</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                {analysisResult.recommended_assessments.map((rec: any, i: number) => (
                  <div key={i} style={{
                    padding: '0.85rem 1rem',
                    borderRadius: '8px',
                    backgroundColor: 'rgba(139, 92, 246, 0.08)',
                    border: '1px solid rgba(139, 92, 246, 0.25)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{rec.title}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{rec.match_reason}</div>
                    </div>
                    <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>Recommended</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Advisory Summary */}
            <div style={{
              padding: '1rem',
              borderRadius: '8px',
              backgroundColor: 'rgba(255, 255, 255, 0.02)',
              border: '1px solid var(--border-color)',
              fontSize: '0.85rem',
              lineHeight: '1.5',
              color: 'var(--text-muted)',
              marginBottom: '1.5rem',
            }}>
              <strong>Recruiter Summary:</strong> {analysisResult.advisory_summary}
            </div>

            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button
                onClick={() => setAnalysisResult(null)}
                className="btn btn-secondary"
                style={{ flex: 1 }}
              >
                Analyze Another Resume
              </button>
              <button
                onClick={onClose}
                className="btn btn-primary"
                style={{ flex: 1 }}
              >
                Done
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
