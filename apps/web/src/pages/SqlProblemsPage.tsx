import React, { useEffect, useState } from 'react';
import { apiRequest } from '../api/client';
import { Database, Plus, Play, ChevronRight, CheckCircle2, AlertCircle, Table } from 'lucide-react';
import { CodeEditor } from '../components/CodeEditor';

export const SqlProblemsPage: React.FC = () => {
  const [problems, setProblems] = useState<any[]>([]);
  const [selectedProblem, setSelectedProblem] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // SQL Query Runner
  const [activeQuery, setActiveQuery] = useState<string>('SELECT * FROM customers;');
  const [runResult, setRunResult] = useState<any | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  // Create Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [title, setTitle] = useState('');
  const [slug, setSlug] = useState('');
  const [desc, setDesc] = useState('');
  const [difficulty, setDifficulty] = useState('MEDIUM');
  const [points, setPoints] = useState(10);
  const [schemaSql, setSchemaSql] = useState(`CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    salary INTEGER NOT NULL
);

INSERT INTO employees VALUES
(1, 'Alice', 'Engineering', 90000),
(2, 'Bob', 'Engineering', 85000),
(3, 'Charlie', 'Marketing', 65000);`);
  const [solutionSql, setSolutionSql] = useState('SELECT department, AVG(salary) as avg_sal FROM employees GROUP BY department;');

  const loadProblems = async () => {
    try {
      setIsLoading(true);
      const res = await apiRequest('/sql/problems');
      setProblems(res);
      if (res.length > 0 && !selectedProblem) {
        setSelectedProblem(res[0]);
        setActiveQuery('SELECT * FROM customers;');
      }
    } catch (err) {
      console.error('Failed to load SQL problems:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadProblems();
  }, []);

  const handleRunQuery = async () => {
    if (!selectedProblem) return;
    setIsRunning(true);
    setRunResult(null);
    try {
      const res = await apiRequest('/sql/run', {
        method: 'POST',
        body: JSON.stringify({
          problem_id: selectedProblem.id,
          query: activeQuery,
        }),
      });
      setRunResult(res);
    } catch (err: any) {
      setRunResult({ status: 'ERROR', error_message: err.message || 'Execution error' });
    } finally {
      setIsRunning(false);
    }
  };

  const handleCreateProblem = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const created = await apiRequest('/sql/problems', {
        method: 'POST',
        body: JSON.stringify({
          title,
          slug,
          description_markdown: desc,
          difficulty,
          points: Number(points),
          schema_sql: schemaSql,
          solution_sql: solutionSql,
        }),
      });
      setShowCreateModal(false);
      await loadProblems();
      setSelectedProblem(created);
    } catch (err: any) {
      alert(err.message || 'Failed to create SQL problem');
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '2rem auto', padding: '0 1.5rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.85rem', marginBottom: '0.35rem' }}>SQL Challenges Sandbox</h1>
          <p style={{ fontSize: '0.95rem' }}>Relational database query challenges with dynamic in-memory schema verification</p>
        </div>

        <button onClick={() => setShowCreateModal(true)} className="btn btn-primary">
          <Plus size={16} /> New SQL Challenge
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '1.75rem', alignItems: 'start' }}>
        {/* Left: Problems List */}
        <div className="card" style={{ padding: '1rem' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', padding: '0 0.5rem' }}>SQL Problems</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {problems.map((p) => {
              const isSelected = selectedProblem?.id === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => {
                    setSelectedProblem(p);
                    setRunResult(null);
                  }}
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
                      {p.difficulty} • {p.points} pts
                    </div>
                  </div>
                  <ChevronRight size={16} color={isSelected ? 'var(--primary)' : 'var(--text-dim)'} />
                </button>
              );
            })}
          </div>
        </div>

        {/* Right: SQL Editor & Output Grid */}
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
                </div>
              </div>

              {/* Problem Prompt */}
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

              {/* Schema SQL Preview Box */}
              <div style={{ marginBottom: '1.5rem' }}>
                <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Database size={15} color="var(--primary)" /> Sandbox Schema & Sample Data
                </label>
                <pre style={{
                  padding: '0.85rem 1rem',
                  borderRadius: '8px',
                  backgroundColor: '#070A13',
                  border: '1px solid var(--border-color)',
                  color: 'var(--text-muted)',
                  fontSize: '0.8rem',
                  maxHeight: '140px',
                  overflowY: 'auto',
                }}>
                  {selectedProblem.schema_sql}
                </pre>
              </div>

              {/* SQL Query Editor */}
              <div style={{ marginBottom: '1.2rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <label className="form-label" style={{ marginBottom: 0 }}>SQL Query</label>
                  <button
                    onClick={handleRunQuery}
                    className="btn btn-primary btn-sm"
                    disabled={isRunning}
                  >
                    <Play size={14} /> {isRunning ? 'Running Query...' : 'Execute SQL'}
                  </button>
                </div>

                <CodeEditor
                  value={activeQuery}
                  onChange={setActiveQuery}
                  language="sql"
                  languages={['sql']}
                  height="180px"
                />
              </div>

              {/* Query Result Grid */}
              {runResult && (
                <div style={{ marginTop: '1.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.9rem', fontWeight: 700 }}>
                      <Table size={16} color="var(--primary)" /> Query Results ({runResult.row_count || 0} rows)
                    </div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                      {runResult.execution_time_ms}ms
                    </span>
                  </div>

                  {runResult.error_message ? (
                    <div className="alert alert-error">
                      <AlertCircle size={16} /> <span>{runResult.error_message}</span>
                    </div>
                  ) : runResult.rows && runResult.rows.length > 0 ? (
                    <div className="table-container" style={{ maxHeight: '240px', overflowY: 'auto' }}>
                      <table>
                        <thead>
                          <tr>
                            {runResult.columns.map((c: string) => (
                              <th key={c}>{c}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {runResult.rows.map((row: any, i: number) => (
                            <tr key={i}>
                              {runResult.columns.map((c: string) => (
                                <td key={c} style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>
                                  {String(row[c] ?? 'NULL')}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
                      Query returned 0 rows.
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              Select an SQL problem from the left to test queries.
            </div>
          )}
        </div>
      </div>

      {/* Create SQL Problem Modal */}
      {showCreateModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.75)', backdropFilter: 'blur(6px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '1rem',
        }}>
          <div className="card" style={{ maxWidth: '640px', width: '100%', maxHeight: '90vh', overflowY: 'auto', padding: '2rem' }}>
            <h3 style={{ marginBottom: '0.5rem' }}>Author SQL Challenge</h3>
            <form onSubmit={handleCreateProblem}>
              <div className="form-group">
                <label className="form-label">Problem Title *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Department High Earners"
                  value={title}
                  onChange={(e) => {
                    setTitle(e.target.value);
                    setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9]/g, '-'));
                  }}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Problem Statement *</label>
                <textarea
                  className="form-textarea"
                  rows={3}
                  placeholder="What should candidate SQL query calculate?"
                  value={desc}
                  onChange={(e) => setDesc(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Schema DDL & Sample INSERTs *</label>
                <textarea
                  className="form-textarea"
                  rows={4}
                  value={schemaSql}
                  onChange={(e) => setSchemaSql(e.target.value)}
                  style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Reference Solution SQL Query *</label>
                <textarea
                  className="form-textarea"
                  rows={3}
                  value={solutionSql}
                  onChange={(e) => setSolutionSql(e.target.value)}
                  style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}
                  required
                />
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                  Create SQL Challenge
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
