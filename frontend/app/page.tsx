'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import FileTree from '../components/FileTree';
import MermaidView from '../components/MermaidView';
import './globals.css';

type LearningPathItem = {
  file_path: string;
  stage: string;
  stage_order: number;
  priority: number;
  description: string;
};

type AnalyzeResult = {
  repo_id: string;
  tree: any[];
  files: any[];
  mermaid: string;
  learning_path: LearningPathItem[];
  annotated_tree: string;
  file_annotations: Record<string, string>;
};

type ChatMessage = {
  role: 'user' | 'assistant';
  content: string;
};

type ProviderInfo = {
  id: string;
  name: string;
  available: string;  // "true" | "false"
};

type HistoryEntry = {
  repo_id: string;
  repo_url: string;
  commit_hash: string;
  analyzed_at: string;
};

const API_BASE = 'http://localhost:8000';

export default function HomePage() {
  const [repoUrl, setRepoUrl] = useState('https://github.com/tiangolo/fastapi');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalyzeResult | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [asking, setAsking] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // ── Provider 切换 ──
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [provider, setProvider] = useState('deepseek');

  // ── 历史记录 ──
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const historyRef = useRef<HTMLDivElement>(null);

  // 点击外部关闭下拉
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (historyRef.current && !historyRef.current.contains(e.target as Node)) {
        setShowHistory(false);
      }
    }
    if (showHistory) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showHistory]);

  // ── 暗色主题 ──
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    // 优先读取 localStorage，其次系统偏好
    const stored = localStorage.getItem('theme');
    if (stored === 'dark') {
      setDarkMode(true);
      document.documentElement.setAttribute('data-theme', 'dark');
    } else if (stored === 'light') {
      setDarkMode(false);
      document.documentElement.removeAttribute('data-theme');
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setDarkMode(true);
      document.documentElement.setAttribute('data-theme', 'dark');
    }
  }, []);

  function toggleTheme() {
    const next = !darkMode;
    setDarkMode(next);
    if (next) {
      document.documentElement.setAttribute('data-theme', 'dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
      localStorage.setItem('theme', 'light');
    }
  }

  // 获取可用 Provider 列表
  useEffect(() => {
    fetch(`${API_BASE}/api/config`)
      .then((res) => res.json())
      .then((data) => {
        if (data.providers) {
          setProviders(data.providers);
          // 如果当前 provider 不可用，自动切换到第一个可用的
          const available = data.providers.filter((p: ProviderInfo) => p.available === 'true');
          if (available.length > 0) {
            const currentAvailable = available.find((p: ProviderInfo) => p.id === provider);
            if (!currentAvailable) {
              setProvider(available[0].id);
            }
          }
        }
      })
      .catch(() => {});
  }, []);

  // 获取分析历史
  useEffect(() => {
    refreshHistory();
  }, []);

  function refreshHistory() {
    fetch(`${API_BASE}/api/history`)
      .then((res) => res.json())
      .then((data) => {
        if (data.history) setHistory(data.history);
      })
      .catch(() => {});
  }

  async function clearHistory() {
    if (!window.confirm('确定要清除所有分析缓存与历史记录吗？此操作不可撤销。')) return;
    try {
      const res = await fetch(`${API_BASE}/api/history`, { method: 'DELETE' });
      if (res.ok) {
        setHistory([]);
        setShowHistory(false);
      }
    } catch { /* ignore */ }
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function analyze(force = false) {
    setLoading(true);
    setMessages([]);
    try {
      const res = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: repoUrl, force }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Analyze failed');
      setResult(data);
      refreshHistory();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  }

  function analyzeFromHistory(entry: HistoryEntry) {
    setRepoUrl(entry.repo_url);
    // 使用 requestAnimationFrame 确保 setRepoUrl 生效后再发请求
    requestAnimationFrame(async () => {
      setLoading(true);
      setMessages([]);
      try {
        const res = await fetch(`${API_BASE}/api/analyze`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ repo_url: entry.repo_url }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Analyze failed');
        setResult(data);
        refreshHistory();
      } catch (err: any) {
        alert(err.message);
      } finally {
        setLoading(false);
      }
    });
  }

  async function sendMessage(question: string, filePath?: string) {
    if (!result || asking) return;

    const userMsg: ChatMessage = { role: 'user', content: question };
    setMessages((prev) => [...prev, userMsg]);
    setAsking(true);

    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const res = await fetch(`${API_BASE}/api/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_id: result.repo_id,
          question,
          file_path: filePath || null,
          history,
          provider,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Ask failed');
      setMessages((prev) => [...prev, { role: 'assistant', content: data.answer }]);
    } catch (err: any) {
      setMessages((prev) => [...prev, { role: 'assistant', content: `❌ 出错了：${err.message}` }]);
    } finally {
      setAsking(false);
    }
  }

  function handleFileClick(path: string) {
    const question = `请详细解释 \`${path}\` 这个文件的作用、结构和关键代码。`;
    sendMessage(question, path);
  }

  function handleSend() {
    const trimmed = inputValue.trim();
    if (!trimmed || asking) return;
    setInputValue('');
    sendMessage(trimmed);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function groupByStage(items: LearningPathItem[]) {
    const groups: { stage: string; items: LearningPathItem[] }[] = [];
    const seen = new Set<string>();
    for (const item of items) {
      if (!seen.has(item.stage)) {
        seen.add(item.stage);
        groups.push({ stage: item.stage, items: [] });
      }
      groups[groups.length - 1].items.push(item);
    }
    return groups;
  }

  function shortName(filePath: string): string {
    const parts = filePath.replace(/\\/g, '/').split('/');
    return parts.length <= 2 ? filePath : parts.slice(-2).join('/');
  }

  function providerName(): string {
    const p = providers.find((x) => x.id === provider);
    return p ? p.name : (provider === 'kimi' ? 'Kimi' : 'DeepSeek');
  }

  function timeAgo(isoString: string): string {
    const diff = Date.now() - new Date(isoString).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return '刚刚';
    if (mins < 60) return `${mins} 分钟前`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours} 小时前`;
    const days = Math.floor(hours / 24);
    return `${days} 天前`;
  }

  function shortRepoUrl(url: string): string {
    try {
      const parts = new URL(url).pathname.split('/').filter(Boolean);
      return parts.slice(-2).join('/');
    } catch {
      return url.replace(/https?\:\/\/github\.com\//, '');
    }
  }

  return (
    <main className="container">
      {/* ── 右上角小组件 ── */}
      <div className="top-right-widgets">
        {/* 主题切换 */}
        <button
          className="theme-toggle-btn"
          onClick={toggleTheme}
          title={darkMode ? '切换到亮色主题' : '切换到暗色主题'}
        >
          {darkMode ? (
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="5"/>
              <line x1="12" y1="1" x2="12" y2="3"/>
              <line x1="12" y1="21" x2="12" y2="23"/>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
              <line x1="1" y1="12" x2="3" y2="12"/>
              <line x1="21" y1="12" x2="23" y2="12"/>
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
            </svg>
          )}
        </button>

        {/* 历史记录时钟 Widget */}
        {history.length > 0 && (
          <div className={`history-widget ${showHistory ? 'open' : ''}`} ref={historyRef}>
            <button
              className="history-trigger"
              onClick={() => setShowHistory(!showHistory)}
              title="分析历史"
            >
              <svg className="history-clock-icon" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
              <span className="history-badge">{history.length}</span>
            </button>
            <div className="history-dropdown">
              <div className="history-dropdown-header">
                <span>最近分析</span>
                <div className="history-header-actions">
                  <button
                    className="history-delete-btn"
                    onClick={clearHistory}
                    title="清除所有历史"
                  >
                    <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="3 6 5 6 21 6"/>
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                  </button>
                  <button
                    className="history-close-btn"
                    onClick={() => setShowHistory(false)}
                    title="关闭"
                  >
                    ✕
                  </button>
                </div>
              </div>
              {history.map((entry) => (
                <button
                  key={entry.repo_id}
                  className="history-dropdown-item"
                  onClick={() => { analyzeFromHistory(entry); setShowHistory(false); }}
                >
                  <span className="history-dropdown-repo">{shortRepoUrl(entry.repo_url)}</span>
                  <span className="history-dropdown-time">{timeAgo(entry.analyzed_at)}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      <section className="header">
        <h1>Code AI Guide</h1>
        <p>输入 GitHub 仓库 URL，生成文件树、架构图、学习路径，并与 AI 对话学习代码。</p>
      </section>

      <section className="card form">
        <input value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)} placeholder="GitHub repository URL" />
        <div className="provider-select">
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
          >
            {providers.length > 0 ? (
              providers.map((p) => (
                <option key={p.id} value={p.id} disabled={p.available !== 'true'}>
                  {p.name}{p.available !== 'true' ? ' (未配置)' : ''}
                </option>
              ))
            ) : (
              <>
                <option value="deepseek">DeepSeek-v4-Pro</option>
                <option value="kimi">Kimi-K2.6</option>
              </>
            )}
          </select>
        </div>
        <button className="primary-btn" onClick={() => analyze()} disabled={loading}>{loading ? '分析中' : '开始分析'}</button>
        <button
          className="refresh-btn"
          onClick={() => analyze(true)}
          disabled={loading}
          title="强制重新分析（忽略缓存）"
        >
          ⟳
        </button>
      </section>

      {result && (
        <section className="grid">
          <div className="card">
            <h2>文件树</h2>
            <FileTree nodes={result.tree} onSelect={handleFileClick} annotations={result.file_annotations} />
          </div>

          <div className="card">
            <h2>架构图</h2>
            <MermaidView chart={result.mermaid} />
            <h2>学习路径</h2>
            <div className="learning-path">
              {groupByStage(result.learning_path).map((group) => (
                <div key={group.stage} className="path-stage">
                  <h3 className="path-stage-title">
                    <span className="stage-dot" />
                    {group.stage}
                  </h3>
                  <ol className="path-list">
                    {group.items.map((item) => (
                      <li key={item.file_path} className="path-item">
                        <button
                          className="tree-file path-file-btn"
                          onClick={() => handleFileClick(item.file_path)}
                        >
                          {shortName(item.file_path)}
                        </button>
                        <span className="path-desc">{item.description}</span>
                        <span className="path-priority" title="优先级分数">
                          {item.priority}
                        </span>
                      </li>
                    ))}
                  </ol>
                </div>
              ))}
            </div>
          </div>

          <div className="card chat-panel">
            <h2>Ask AI ({providerName()})</h2>
            <div className="chat-messages">
              {messages.length === 0 ? (
                <div className="chat-empty">
                  <p>👈 点击左侧文件或学习路径开始解释</p>
                  <p>或直接在下方输入框向 {providerName()} 提问</p>
                  <p className="chat-hints">试试问："这个项目的核心架构是什么？"、"请求处理流程是怎样的？"</p>
                </div>
              ) : (
                messages.map((msg, i) => (
                  <div key={i} className={`chat-bubble ${msg.role}`}>
                    <div className="chat-role">{msg.role === 'user' ? '🧑 你' : `🤖 AI (${providerName()})`}</div>
                    <div className="markdown-content">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                    </div>
                  </div>
                ))
              )}
              {asking && (
                <div className="chat-bubble assistant">
                  <div className="chat-role">🤖 AI ({providerName()})</div>
                  <div className="chat-typing">思考中<span className="dots" /></div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
            <div className="chat-input-area">
              <input
                className="chat-input"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="向 AI 提问关于这个仓库的任何问题..."
                disabled={asking}
              />
              <button className="chat-send-btn" onClick={handleSend} disabled={asking || !inputValue.trim()}>
                发送
              </button>
            </div>
          </div>
        </section>
      )}
    </main>
  );
}
