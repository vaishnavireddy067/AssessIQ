import React, { useEffect, useState } from 'react';
import { apiRequest } from '../api/client';
import { Code2, Plus, Terminal, CheckCircle2, Play, ChevronRight, HelpCircle } from 'lucide-react';
import { CodeEditor } from '../components/CodeEditor';

export const CodingProblemsPage: React.FC = () => {
  const [problems, setProblems] = useState<any[]>([]);
  const [selectedProblem, setSelectedProblem] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Test Run in Recruiter Sandbox
  const [activeCode, setActiveCode] = useState<string>('');
  const [activeLang, setActiveLang] = useState<string>('python');
  const [customInput, setCustomInput] = useState<string>('');
  const [runOutput, setRunOutput] = useState<any | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  // Create Problem Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [title, setTitle] = useState('');
  const [slug, setSlug] = useState('');
  const [desc, setDesc] = useState('');
  const [difficulty, setDifficulty] = useState('MEDIUM');
  const [points, setPoints] = useState(10);
  const [timeLimit, setTimeLimit] = useState(2000);
  const [pyStarter, setPyStarter] = useState('import sys\n\ndef solve():\n    # Read from sys.stdin\n    pass\n\nsolve()\n');
  const [jsStarter, setJsStarter] = useState('const fs = require(\'fs\');\n\nfunction solve() {\n    // Read input from fs.readFileSync(0, \'utf-8\')\n}\nsolve();\n');
  const [testCases, setTestCases] = useState([
    { input_data: '9\n2 7 11 15', expected_output: '0 1', is_hidden: false, explanation: 'Sample 1' },
    { input_data: '6\n3 2 4', expected_output: '1 2', is_hidden: false, explanation: 'Sample 2' },
    { input_data: '6\n3 3', expected_output: '0 1', is_hidden: true, explanation: 'Hidden benchmark' },
  ]);

  const loadProblems = async () => {
    try {
      setIsLoading(true);
      const res = await apiRequest('/coding/problems');
      setProblems(res);
      if (res.length > 0 && !selectedProblem) {
        setSelectedProblem(res[0]);
        setActiveCode(res[0].starter_code?.python || '');
      }
    } catch (err) {
      console.error('Failed to load coding problems:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadProblems();
  }, []);

  const handleSelectProblem = (p: any) => {
    setSelectedProblem(p);
    setActiveCode(p.starter_code?.[activeLang] || p.starter_code?.python || '');
    setRunOutput(null);
  };

  const handleRunCode = async () => {
    if (!selectedProblem) return;
    setIsRunning(true);
    setRunOutput(null);
    try {
      const res = await apiRequest('/coding/run', {
        method: 'POST',
        body: JSON.stringify({
          language: activeLang,
          code: activeCode,
          problem_id: selectedProblem.id,
          custom_input: customInput || undefined,
        }),
      });
      setRunOutput(res);
    } catch (err: any) {
      setRunOutput({ status: 'ERROR', stderr: err.message || 'Execution failed' });
    } finally {
      setIsRunning(false);
    }
  };

  const handleCreateProblem = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const created = await apiRequest('/coding/problems', {
        method: 'POST',
        body: JSON.stringify({
          title,
          slug,
          description_markdown: desc,
          difficulty,
          points: Number(points),
          time_limit_ms: Number(timeLimit),
          starter_code: {
            python: pyStarter,
            javascript: jsStarter,
          },
          test_cases: testCases,
        }),
      });
      setShowCreateModal(false);
      await loadProblems();
      setSelectedProblem(created);
    } catch (err: any) {
      alert(err.message || 'Failed to create coding problem');
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '2rem auto', padding: '0 1.5rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.85rem', marginBottom: '0.35rem' }}>Coding Challenges Sandbox</h1>
          <p style={{ fontSize: '0.95rem' }}>Multi-language algorithmic programming problems with sandboxed test case grading</p>
        </div>

        <button onClick={() => setShowCreateModal(true)} className="btn btn-primary">
          <Plus size={16} /> New Coding Challenge
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '1.75rem', alignItems: 'start' }}>
        {/* Left: Problems List */}
        <div className="card" style={{ padding: '1rem' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', padding: '0 0.5rem' }}>Problem Bank</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {problems.map((p) => {
              const isSelected = selectedProblem?.id === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => handleSelectProblem(p)}
                  style={{
                    padding: '0.85rem 1rem',
                    borderRadius: '8px',
                    backgroundColor: isSelected ? 'rgba(99, 102, 241, 0.15)' : 'rgba(255, 255, 255, 0.02)',
                    border: `1px solid ${isSelected ? 'var(--primary)' : 'var(--border-color)'}`,
                    color: isSelected ? '#FFF' : 'var(--text-main)',
                    textAlign: 'left',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{p.title}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {p.difficulty} • {p.points} pts • {p.test_cases?.length || 0} cases
                    </div>
                  </div>
                  <ChevronRight size={16} color={isSelected ? 'var(--primary)' : 'var(--text-dim)'} />
                </button>
              );
            })}
          </div>
        </div>

        {/* Right: Problem Sandbox & Live Runner */}
        <div className="card">
          {selectedProblem ? (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
                    <h2 style={{ fontSize: '1.4rem' }}>{selectedProblem.title}</h2>
                    <span className="badge badge-primary">{selectedProblem.difficulty}</span>
                    <span className="badge badge-secondary">{selectedProblem.points} Pts</span>
                  </div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                    Time Limit: {selectedProblem.time_limit_ms}ms • Memory: {selectedProblem.memory_limit_mb}MB
                  </p>
                </div>
              </div>

              {/* Description Markdown */}
              <div style={{
                padding: '1.2rem',
                borderRadius: '8px',
                backgroundColor: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid var(--border-color)',
                fontSize: '0.9rem',
                lineHeight: '1.6',
                marginBottom: '1.5rem',
                whiteSpace: 'pre-wrap',
              }}>
                {selectedProblem.description_markdown}
              </div>

              {/* Interactive Code Editor */}
              <div style={{ marginBottom: '1.2rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <label className="form-label" style={{ marginBottom: 0 }}>Solution Code</label>
                  <button
                    onClick={handleRunCode}
                    className="btn btn-primary btn-sm"
                    disabled={isRunning}
                  >
                    <Play size={14} /> {isRunning ? 'Executing...' : 'Run Test Cases'}
                  </button>
                </div>

                <CodeEditor
                  value={activeCode}
                  onChange={setActiveCode}
                  language={activeLang}
                  onLanguageChange={(l) => {
                    setActiveLang(l);
                    setActiveCode(selectedProblem.starter_code?.[l] || '');
                  }}
                  onReset={() => setActiveCode(selectedProblem.starter_code?.[activeLang] || '')}
                  height="280px"
                />
              </div>

              {/* Execution Output Panel */}
              {runOutput && (
                <div style={{
                  padding: '1rem',
                  borderRadius: '8px',
                  backgroundColor: '#070A13',
                  border: '1px solid var(--border-color)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.85rem',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <Terminal size={15} color="var(--primary)" />
                      <span style={{ fontWeight: 700 }}>Execution Terminal</span>
                    </div>
                    <span className={`badge ${
                      runOutput.status === 'ACCEPTED' || runOutput.passed_all ? 'badge-success' : 'badge-danger'
                    }`}>
                      {runOutput.status} ({runOutput.execution_time_ms}ms)
                    </span>
                  </div>

                  {runOutput.test_case_results && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginTop: '0.5rem' }}>
                      {runOutput.test_case_results.map((tc: any, i: number) => (
                        <div key={i} style={{
                          padding: '0.45rem 0.75rem',
                          borderRadius: '6px',
                          backgroundColor: tc.passed ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          fontSize: '0.8rem',
                        }}>
                          <span>Case {i + 1}: {tc.input_data.replace(/\n/g, ' ')} → {tc.expected_output}</span>
                          <span style={{ color: tc.passed ? 'var(--success)' : 'var(--danger)', fontWeight: 700 }}>
                            {tc.passed ? 'PASSED' : 'FAILED'}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  {runOutput.stderr && (
                    <pre style={{ color: 'var(--danger)', marginTop: '0.5rem', whiteSpace: 'pre-wrap' }}>
                      {runOutput.stderr}
                    </pre>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              Select a coding challenge from the left to view details and run code.
            </div>
          )}
        </div>
      </div>

      {/* Create Coding Challenge Modal */}
      {showCreateModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.75)', backdropFilter: 'blur(6px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '1rem',
        }}>
          <div className="card" style={{ maxWidth: '640px', width: '100%', maxHeight: '90vh', overflowY: 'auto', padding: '2rem' }}>
            <h3 style={{ marginBottom: '0.5rem' }}>Author Coding Challenge</h3>
            <form onSubmit={handleCreateProblem}>
              <div className="form-group">
                <label className="form-label">Problem Title *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Invert Binary Tree"
                  value={title}
                  onChange={(e) => {
                    setTitle(e.target.value);
                    setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9]/g, '-'));
                  }}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Problem Description & Constraints *</label>
                <textarea
                  className="form-textarea"
                  rows={4}
                  placeholder="Explain input format, output format, and algorithmic constraints..."
                  value={desc}
                  onChange={(e) => setDesc(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Difficulty</label>
                  <select
                    className="form-select"
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value)}
                  >
                    <option value="EASY">Easy</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="HARD">Hard</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Points</label>
                  <input
                    type="number"
                    className="form-input"
                    value={points}
                    onChange={(e) => setPoints(Number(e.target.value))}
                    required
                  />
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                  Create Challenge
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
