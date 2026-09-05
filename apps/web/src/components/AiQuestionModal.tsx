import React, { useState } from 'react';
import { apiRequest } from '../api/client';
import { Sparkles, Loader2, Plus, CheckCircle2, XCircle } from 'lucide-react';

interface GeneratedOption {
  option_text: string;
  is_correct: boolean;
}

interface GeneratedMCQ {
  title: string;
  content_markdown: string;
  difficulty: string;
  points: number;
  explanation: string;
  options: GeneratedOption[];
  tags: string[];
}

interface AiQuestionModalProps {
  bankId: string;
  onClose: () => void;
  onQuestionsAdded: () => void;
}

export const AiQuestionModal: React.FC<AiQuestionModalProps> = ({ bankId, onClose, onQuestionsAdded }) => {
  const [topic, setTopic] = useState('');
  const [count, setCount] = useState(3);
  const [difficulty, setDifficulty] = useState('MEDIUM');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generated, setGenerated] = useState<GeneratedMCQ[]>([]);
  const [selectedIndices, setSelectedIndices] = useState<Set<number>>(new Set());
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedCount, setSavedCount] = useState(0);

  const handleGenerate = async () => {
    if (!topic.trim()) return;
    setIsGenerating(true);
    setError(null);
    setGenerated([]);
    setSelectedIndices(new Set());
    setSavedCount(0);

    try {
      const res = await apiRequest('/ai/generate-questions', {
        method: 'POST',
        body: JSON.stringify({ topic, count, difficulty }),
      });
      setGenerated(res);
      // Select all by default
      setSelectedIndices(new Set(res.map((_: any, i: number) => i)));
    } catch (err: any) {
      setError(err.message || 'Failed to generate questions');
    } finally {
      setIsGenerating(false);
    }
  };

  const toggleSelect = (index: number) => {
    const updated = new Set(selectedIndices);
    if (updated.has(index)) updated.delete(index);
    else updated.add(index);
    setSelectedIndices(updated);
  };

  const handleSaveSelected = async () => {
    setIsSaving(true);
    setError(null);
    let saved = 0;

    for (const idx of selectedIndices) {
      const q = generated[idx];
      try {
        await apiRequest(`/questions/banks/${bankId}/questions`, {
          method: 'POST',
          body: JSON.stringify({
            title: q.title,
            content_markdown: q.content_markdown,
            difficulty: q.difficulty,
            points: q.points,
            explanation: q.explanation,
            options: q.options,
            tags: q.tags,
          }),
        });
        saved++;
      } catch (err) {
        console.error('Failed to save question:', err);
      }
    }

    setSavedCount(saved);
    setIsSaving(false);

    if (saved > 0) {
      onQuestionsAdded();
    }
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.8)', backdropFilter: 'blur(8px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '1rem',
    }}>
      <div className="card" style={{ maxWidth: '720px', width: '100%', maxHeight: '90vh', overflowY: 'auto', padding: '2rem' }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <div style={{
              width: '38px', height: '38px', borderRadius: '10px',
              background: 'linear-gradient(135deg, #8B5CF6, #6366F1)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 0 20px rgba(139, 92, 246, 0.4)',
            }}>
              <Sparkles size={20} color="#FFF" />
            </div>
            <div>
              <h3 style={{ fontSize: '1.2rem', margin: 0 }}>✨ AI Question Generator</h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', margin: 0 }}>
                Generate high-quality MCQs from any topic instantly
              </p>
            </div>
          </div>
          <button onClick={onClose} className="btn btn-secondary btn-sm">Close</button>
        </div>

        {/* Generation Form */}
        {generated.length === 0 && !savedCount && (
          <div>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.4rem', display: 'block' }}>
                Topic / Skill
              </label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Docker & Containers, React Hooks, Kubernetes..."
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
              <div>
                <label style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.4rem', display: 'block' }}>
                  Number of Questions
                </label>
                <select
                  className="form-input"
                  value={count}
                  onChange={(e) => setCount(Number(e.target.value))}
                  style={{ width: '100%' }}
                >
                  {[1, 2, 3, 5, 10].map((n) => (
                    <option key={n} value={n}>{n} Questions</option>
                  ))}
                </select>
              </div>
              <div>
                <label style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.4rem', display: 'block' }}>
                  Difficulty
                </label>
                <select
                  className="form-input"
                  value={difficulty}
                  onChange={(e) => setDifficulty(e.target.value)}
                  style={{ width: '100%' }}
                >
                  <option value="EASY">Easy</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HARD">Hard</option>
                </select>
              </div>
            </div>

            {error && (
              <div className="alert alert-error" style={{ marginBottom: '1rem', fontSize: '0.85rem' }}>
                <XCircle size={14} /> {error}
              </div>
            )}

            <button
              onClick={handleGenerate}
              className="btn btn-primary"
              disabled={isGenerating || !topic.trim()}
              style={{ width: '100%', padding: '0.85rem', fontSize: '1rem' }}
            >
              {isGenerating ? (
                <><Loader2 size={18} className="spin" /> Generating with AI...</>
              ) : (
                <><Sparkles size={18} /> Generate Questions</>
              )}
            </button>
          </div>
        )}

        {/* Generated Questions Preview */}
        {generated.length > 0 && !savedCount && (
          <div>
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              marginBottom: '1rem', padding: '0.75rem', borderRadius: '8px',
              backgroundColor: 'rgba(139, 92, 246, 0.1)', border: '1px solid rgba(139, 92, 246, 0.3)',
            }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>
                {generated.length} questions generated • {selectedIndices.size} selected
              </span>
              <button
                onClick={() => {
                  if (selectedIndices.size === generated.length) {
                    setSelectedIndices(new Set());
                  } else {
                    setSelectedIndices(new Set(generated.map((_, i) => i)));
                  }
                }}
                className="btn btn-secondary btn-sm"
                style={{ fontSize: '0.7rem' }}
              >
                {selectedIndices.size === generated.length ? 'Deselect All' : 'Select All'}
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.5rem' }}>
              {generated.map((q, i) => {
                const isSelected = selectedIndices.has(i);
                return (
                  <div
                    key={i}
                    onClick={() => toggleSelect(i)}
                    style={{
                      padding: '1rem',
                      borderRadius: '8px',
                      backgroundColor: isSelected ? 'rgba(99, 102, 241, 0.08)' : 'rgba(255, 255, 255, 0.02)',
                      border: `1px solid ${isSelected ? 'var(--primary)' : 'var(--border-color)'}`,
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <div style={{
                          width: '20px', height: '20px', borderRadius: '4px',
                          backgroundColor: isSelected ? 'var(--primary)' : 'transparent',
                          border: `2px solid ${isSelected ? 'var(--primary)' : 'var(--text-dim)'}`,
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                        }}>
                          {isSelected && <CheckCircle2 size={14} color="#FFF" />}
                        </div>
                        <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{q.title}</span>
                      </div>
                      <div style={{ display: 'flex', gap: '0.3rem' }}>
                        <span className="badge badge-secondary" style={{ fontSize: '0.6rem' }}>{q.difficulty}</span>
                        <span className="badge badge-primary" style={{ fontSize: '0.6rem' }}>{q.points} pts</span>
                      </div>
                    </div>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: '0 0 0.5rem 0' }}>{q.content_markdown}</p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                      {q.options.map((opt, oi) => (
                        <div key={oi} style={{
                          fontSize: '0.75rem', padding: '0.3rem 0.5rem', borderRadius: '4px',
                          backgroundColor: opt.is_correct ? 'rgba(16, 185, 129, 0.1)' : 'transparent',
                          color: opt.is_correct ? 'var(--success)' : 'var(--text-muted)',
                        }}>
                          {opt.is_correct ? '✓ ' : '  '}{opt.option_text}
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>

            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button
                onClick={() => { setGenerated([]); setSelectedIndices(new Set()); }}
                className="btn btn-secondary"
                style={{ flex: 1 }}
              >
                ← Regenerate
              </button>
              <button
                onClick={handleSaveSelected}
                className="btn btn-primary"
                disabled={isSaving || selectedIndices.size === 0}
                style={{ flex: 1 }}
              >
                {isSaving ? (
                  <><Loader2 size={16} className="spin" /> Saving...</>
                ) : (
                  <><Plus size={16} /> Save {selectedIndices.size} to Bank</>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Success Confirmation */}
        {savedCount > 0 && (
          <div style={{ textAlign: 'center', padding: '2rem 0' }}>
            <div style={{
              width: '56px', height: '56px', borderRadius: '50%',
              backgroundColor: 'rgba(16, 185, 129, 0.15)',
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
              marginBottom: '1rem',
            }}>
              <CheckCircle2 size={32} color="var(--success)" />
            </div>
            <h3 style={{ fontSize: '1.3rem', marginBottom: '0.3rem' }}>
              {savedCount} Questions Added!
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
              AI-generated questions have been saved to your question bank.
            </p>
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
              <button onClick={() => { setGenerated([]); setSavedCount(0); setTopic(''); }} className="btn btn-secondary">
                Generate More
              </button>
              <button onClick={onClose} className="btn btn-primary">
                Done
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
