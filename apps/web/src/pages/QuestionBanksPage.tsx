import React, { useEffect, useState } from 'react';
import { apiRequest } from '../api/client';
import { Layers, Plus, Trash2, CheckCircle2, FileText, ChevronRight, HelpCircle, Sparkles } from 'lucide-react';
import { AiQuestionModal } from '../components/AiQuestionModal';

export const QuestionBanksPage: React.FC = () => {
  const [banks, setBanks] = useState<any[]>([]);
  const [selectedBank, setSelectedBank] = useState<any | null>(null);
  const [questions, setQuestions] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Create Bank Modal
  const [showBankModal, setShowBankModal] = useState(false);
  const [bankName, setBankName] = useState('');
  const [bankCategory, setBankCategory] = useState('Backend');
  const [bankDesc, setBankDesc] = useState('');

  // Create Question Modal
  const [showQuestionModal, setShowQuestionModal] = useState(false);
  const [qTitle, setQTitle] = useState('');
  const [qContent, setQContent] = useState('');
  const [qDifficulty, setQDifficulty] = useState('MEDIUM');
  const [qPoints, setQPoints] = useState(2.0);
  const [qExplanation, setQExplanation] = useState('');
  const [options, setOptions] = useState([
    { option_text: '', is_correct: true },
    { option_text: '', is_correct: false },
    { option_text: '', is_correct: false },
    { option_text: '', is_correct: false },
  ]);
  const [error, setError] = useState<string | null>(null);
  const [showAiModal, setShowAiModal] = useState(false);

  const loadBanks = async () => {
    try {
      setIsLoading(true);
      const res = await apiRequest('/questions/banks');
      setBanks(res);
      if (res.length > 0 && !selectedBank) {
        setSelectedBank(res[0]);
      }
    } catch (err) {
      console.error('Failed to load banks:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadBanks();
  }, []);

  useEffect(() => {
    const loadQuestions = async () => {
      if (!selectedBank) return;
      try {
        const res = await apiRequest(`/questions/banks/${selectedBank.id}/questions`);
        setQuestions(res);
      } catch (err) {
        console.error('Failed to load questions:', err);
      }
    };
    loadQuestions();
  }, [selectedBank]);

  const handleCreateBank = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const created = await apiRequest('/questions/banks', {
        method: 'POST',
        body: JSON.stringify({
          name: bankName,
          category: bankCategory,
          description: bankDesc,
        }),
      });
      setShowBankModal(false);
      setBankName('');
      setBankDesc('');
      await loadBanks();
      setSelectedBank(created);
    } catch (err: any) {
      alert(err.message || 'Failed to create bank');
    }
  };

  const handleOptionTextChange = (idx: number, text: string) => {
    const updated = [...options];
    updated[idx].option_text = text;
    setOptions(updated);
  };

  const handleSetCorrectOption = (idx: number) => {
    const updated = options.map((opt, i) => ({
      ...opt,
      is_correct: i === idx,
    }));
    setOptions(updated);
  };

  const handleCreateQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!selectedBank) return;

    const validOptions = options.filter((o) => o.option_text.trim().length > 0);
    if (validOptions.length < 2) {
      setError('Please provide at least 2 option choices.');
      return;
    }

    if (!validOptions.some((o) => o.is_correct)) {
      setError('Please mark at least one choice as the correct answer.');
      return;
    }

    try {
      await apiRequest(`/questions/banks/${selectedBank.id}/questions`, {
        method: 'POST',
        body: JSON.stringify({
          title: qTitle,
          content_markdown: qContent,
          difficulty: qDifficulty,
          points: Number(qPoints),
          explanation: qExplanation || undefined,
          options: validOptions,
        }),
      });

      setShowQuestionModal(false);
      setQTitle('');
      setQContent('');
      setQExplanation('');
      setOptions([
        { option_text: '', is_correct: true },
        { option_text: '', is_correct: false },
        { option_text: '', is_correct: false },
        { option_text: '', is_correct: false },
      ]);

      const res = await apiRequest(`/questions/banks/${selectedBank.id}/questions`);
      setQuestions(res);
      await loadBanks();
    } catch (err: any) {
      setError(err.message || 'Failed to create question');
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '2rem auto', padding: '0 1.5rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.85rem', marginBottom: '0.35rem' }}>Question Banks Library</h1>
          <p style={{ fontSize: '0.95rem' }}>Organize technical assessments into modular, reusable question collections</p>
        </div>

        <button onClick={() => setShowBankModal(true)} className="btn btn-primary">
          <Plus size={16} /> New Question Bank
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '1.75rem', alignItems: 'start' }}>
        {/* Left Panel: Bank List */}
        <div className="card" style={{ padding: '1rem' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', padding: '0 0.5rem' }}>Collections</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {banks.map((b) => {
              const isSelected = selectedBank?.id === b.id;
              return (
                <button
                  key={b.id}
                  onClick={() => setSelectedBank(b)}
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
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{b.name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {b.category} • {b.questions_count || 0} questions
                    </div>
                  </div>
                  <ChevronRight size={16} color={isSelected ? 'var(--primary)' : 'var(--text-dim)'} />
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Panel: Selected Bank Questions */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.75rem' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <h2 style={{ fontSize: '1.4rem' }}>{selectedBank?.name}</h2>
                <span className="badge badge-primary">{selectedBank?.category}</span>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                {selectedBank?.description || 'No description for this question collection.'}
              </p>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                onClick={() => setShowAiModal(true)}
                className="btn btn-secondary btn-sm"
                disabled={!selectedBank}
                style={{
                  background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(99, 102, 241, 0.15))',
                  borderColor: 'rgba(139, 92, 246, 0.4)',
                  color: '#A78BFA',
                }}
              >
                <Sparkles size={15} /> ✨ Generate with AI
              </button>
              <button
                onClick={() => setShowQuestionModal(true)}
                className="btn btn-primary btn-sm"
                disabled={!selectedBank}
              >
                <Plus size={16} /> Add Question
              </button>
            </div>
          </div>

          {questions.length === 0 ? (
            <div style={{
              padding: '3rem 1rem',
              textAlign: 'center',
              backgroundColor: 'rgba(255, 255, 255, 0.01)',
              borderRadius: '8px',
              border: '1px dashed var(--border-color)',
            }}>
              <HelpCircle size={40} color="var(--primary)" style={{ margin: '0 auto 0.75rem', opacity: 0.8 }} />
              <div style={{ fontWeight: 600, fontSize: '1rem', marginBottom: '0.3rem' }}>
                No questions in this bank
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-dim)', marginBottom: '1.2rem' }}>
                Create multiple-choice questions with options and explanations.
              </p>
              <button onClick={() => setShowQuestionModal(true)} className="btn btn-primary btn-sm">
                <Plus size={15} /> Add First Question
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
              {questions.map((q, idx) => (
                <div
                  key={q.id}
                  style={{
                    padding: '1.2rem',
                    borderRadius: '10px',
                    backgroundColor: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid var(--border-color)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span className="badge badge-primary" style={{ fontSize: '0.65rem' }}>
                        Q{idx + 1}
                      </span>
                      <span className={`badge ${
                        q.difficulty === 'EASY' ? 'badge-success' :
                        q.difficulty === 'MEDIUM' ? 'badge-warning' : 'badge-danger'
                      }`} style={{ fontSize: '0.65rem' }}>
                        {q.difficulty}
                      </span>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {q.points} pts
                      </span>
                    </div>
                  </div>

                  <h4 style={{ fontSize: '1.05rem', marginBottom: '0.4rem' }}>{q.title}</h4>
                  <p style={{ fontSize: '0.9rem', color: 'var(--text-main)', marginBottom: '1rem' }}>
                    {q.content_markdown}
                  </p>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '0.75rem' }}>
                    {q.options?.map((opt: any) => (
                      <div
                        key={opt.id}
                        style={{
                          padding: '0.6rem 0.85rem',
                          borderRadius: '6px',
                          backgroundColor: opt.is_correct ? 'rgba(16, 185, 129, 0.1)' : 'rgba(255, 255, 255, 0.02)',
                          border: `1px solid ${opt.is_correct ? 'rgba(16, 185, 129, 0.4)' : 'var(--border-color)'}`,
                          fontSize: '0.85rem',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                        }}
                      >
                        <span>{opt.option_text}</span>
                        {opt.is_correct && (
                          <span className="badge badge-success" style={{ fontSize: '0.6rem', padding: '0.1rem 0.35rem' }}>
                            Correct Answer
                          </span>
                        )}
                      </div>
                    ))}
                  </div>

                  {q.explanation && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', backgroundColor: 'rgba(99, 102, 241, 0.05)', padding: '0.6rem 0.85rem', borderRadius: '6px', borderLeft: '3px solid var(--primary)' }}>
                      <strong>Explanation:</strong> {q.explanation}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Create Bank Modal */}
      {showBankModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.75)', backdropFilter: 'blur(6px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '1rem',
        }}>
          <div className="card" style={{ maxWidth: '440px', width: '100%', padding: '2rem' }}>
            <h3 style={{ marginBottom: '0.5rem' }}>New Question Bank</h3>
            <form onSubmit={handleCreateBank}>
              <div className="form-group">
                <label className="form-label">Bank Name *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Distributed Systems & Microservices"
                  value={bankName}
                  onChange={(e) => setBankName(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Category</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Backend / Cloud / Data"
                  value={bankCategory}
                  onChange={(e) => setBankCategory(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Description</label>
                <textarea
                  className="form-textarea"
                  rows={3}
                  placeholder="What topics does this question bank cover?"
                  value={bankDesc}
                  onChange={(e) => setBankDesc(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setShowBankModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                  Create Bank
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Question Modal */}
      {showQuestionModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.75)', backdropFilter: 'blur(6px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '1rem',
        }}>
          <div className="card" style={{ maxWidth: '600px', width: '100%', maxHeight: '90vh', overflowY: 'auto', padding: '2rem' }}>
            <h3 style={{ marginBottom: '0.5rem' }}>Add MCQ Question</h3>
            <p style={{ fontSize: '0.85rem', marginBottom: '1.2rem', color: 'var(--text-muted)' }}>
              Adding to <strong>{selectedBank?.name}</strong>
            </p>

            {error && (
              <div className="alert alert-error">
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleCreateQuestion}>
              <div className="form-group">
                <label className="form-label">Question Title *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Database Index Cardinality"
                  value={qTitle}
                  onChange={(e) => setQTitle(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Question Text (Markdown supported) *</label>
                <textarea
                  className="form-textarea"
                  rows={3}
                  placeholder="Explain the concept or scenario for the candidate..."
                  value={qContent}
                  onChange={(e) => setQContent(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Difficulty</label>
                  <select
                    className="form-select"
                    value={qDifficulty}
                    onChange={(e) => setQDifficulty(e.target.value)}
                  >
                    <option value="EASY">Easy</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="HARD">Hard</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Points Awarded</label>
                  <input
                    type="number"
                    step="0.5"
                    min="0.5"
                    max="10"
                    className="form-input"
                    value={qPoints}
                    onChange={(e) => setQPoints(Number(e.target.value))}
                    required
                  />
                </div>
              </div>

              {/* Options Section */}
              <div style={{ marginTop: '1rem', marginBottom: '1.2rem' }}>
                <label className="form-label" style={{ marginBottom: '0.5rem', display: 'block' }}>
                  Answer Choices (Click radio to mark correct answer) *
                </label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                  {options.map((opt, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                      <input
                        type="radio"
                        name="correctOption"
                        checked={opt.is_correct}
                        onChange={() => handleSetCorrectOption(i)}
                        style={{ cursor: 'pointer', width: '18px', height: '18px' }}
                      />
                      <input
                        type="text"
                        className="form-input"
                        placeholder={`Option ${i + 1}`}
                        value={opt.option_text}
                        onChange={(e) => handleOptionTextChange(i, e.target.value)}
                      />
                    </div>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Explanation (Revealed in recruiter scorecards)</label>
                <textarea
                  className="form-textarea"
                  rows={2}
                  placeholder="Why is this option correct?"
                  value={qExplanation}
                  onChange={(e) => setQExplanation(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setShowQuestionModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                  Save Question
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
