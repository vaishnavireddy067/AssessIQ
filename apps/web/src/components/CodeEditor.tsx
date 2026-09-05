import React from 'react';
import { Code2, RotateCcw, Copy, Check } from 'lucide-react';

interface CodeEditorProps {
  value: string;
  onChange: (val: string) => void;
  language?: string;
  onLanguageChange?: (lang: string) => void;
  languages?: string[];
  onReset?: () => void;
  height?: string;
  readOnly?: boolean;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({
  value,
  onChange,
  language = 'python',
  onLanguageChange,
  languages = ['python', 'javascript'],
  onReset,
  height = '360px',
  readOnly = false,
}) => {
  const [copied, setCopied] = React.useState(false);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const target = e.target as HTMLTextAreaElement;
      const start = target.selectionStart;
      const end = target.selectionEnd;

      // Insert 4 spaces
      const newValue = value.substring(0, start) + '    ' + value.substring(end);
      onChange(newValue);

      setTimeout(() => {
        target.selectionStart = target.selectionEnd = start + 4;
      }, 0);
    }
  };

  const copyCode = () => {
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lineCount = (value.match(/\n/g) || []).length + 1;
  const lineNumbers = Array.from({ length: Math.max(lineCount, 12) }, (_, i) => i + 1);

  return (
    <div style={{
      borderRadius: '10px',
      overflow: 'hidden',
      border: '1px solid var(--border-color)',
      backgroundColor: '#070A13',
      display: 'flex',
      flexDirection: 'column',
    }}>
      {/* Editor Header Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.6rem 1rem',
        backgroundColor: '#0D111E',
        borderBottom: '1px solid var(--border-color)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Code2 size={16} color="var(--primary)" />
          {onLanguageChange && languages.length > 1 ? (
            <select
              value={language}
              onChange={(e) => onLanguageChange(e.target.value)}
              className="form-select"
              style={{
                padding: '0.2rem 0.6rem',
                fontSize: '0.8rem',
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid var(--border-color)',
                width: 'auto',
                color: 'var(--text-main)',
              }}
            >
              {languages.map((l) => (
                <option key={l} value={l}>
                  {l.toUpperCase()}
                </option>
              ))}
            </select>
          ) : (
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              {language}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {onReset && (
            <button
              type="button"
              onClick={onReset}
              className="btn btn-secondary btn-sm"
              title="Reset code"
              style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
            >
              <RotateCcw size={13} /> Reset
            </button>
          )}
          <button
            type="button"
            onClick={copyCode}
            className="btn btn-secondary btn-sm"
            title="Copy code"
            style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
          >
            {copied ? <Check size={13} color="var(--success)" /> : <Copy size={13} />}
          </button>
        </div>
      </div>

      {/* Editor Body with Line Numbers */}
      <div style={{ display: 'flex', height, overflow: 'hidden', position: 'relative' }}>
        {/* Line Numbers Column */}
        <div style={{
          width: '42px',
          backgroundColor: '#090D18',
          borderRight: '1px solid var(--border-color)',
          padding: '0.75rem 0',
          textAlign: 'right',
          userSelect: 'none',
          color: '#4B5563',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.85rem',
          lineHeight: '1.5rem',
          paddingRight: '0.6rem',
        }}>
          {lineNumbers.map((n) => (
            <div key={n}>{n}</div>
          ))}
        </div>

        {/* Textarea Code Input */}
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          readOnly={readOnly}
          spellCheck={false}
          style={{
            flex: 1,
            padding: '0.75rem 1rem',
            backgroundColor: 'transparent',
            border: 'none',
            outline: 'none',
            color: '#E2E8F0',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.875rem',
            lineHeight: '1.5rem',
            resize: 'none',
            whiteSpace: 'pre',
            overflowWrap: 'normal',
            overflowX: 'auto',
          }}
        />
      </div>
    </div>
  );
};
