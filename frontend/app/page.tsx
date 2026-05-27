'use client';

import { useState, useRef, useEffect } from 'react';
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

const API_BASE = 'http://localhost:8000';

export default function HomePage() {
  const [repoUrl, setRepoUrl] = useState('https://github.com/tiangolo/fastapi');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalyzeResult | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [asking, setAsking] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function analyze() {
    setLoading(true);
    setMessages([]);
    try {
      const res = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: repoUrl }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Analyze failed');
      setResult(data);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
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

  return (
    <main className="container">
      <section className="header">
        <h1>Code AI Guide</h1>
        <p>输入 GitHub 仓库 URL，生成文件树、架构图、学习路径，并与 AI 对话学习代码。</p>
      </section>

      <section className="card form">
        <input value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)} placeholder="GitHub repository URL" />
        <button className="primary-btn" onClick={analyze} disabled={loading}>{loading ? '分析中' : '开始分析'}</button>
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
            <h2>Ask AI</h2>
            <div className="chat-messages">
              {messages.length === 0 ? (
                <div className="chat-empty">
                  <p>👈 点击左侧文件或学习路径开始解释</p>
                  <p>或直接在下方输入框向 AI 提问</p>
                  <p className="chat-hints">试试问："这个项目的核心架构是什么？"、"请求处理流程是怎样的？"</p>
                </div>
              ) : (
                messages.map((msg, i) => (
                  <div key={i} className={`chat-bubble ${msg.role}`}>
                    <div className="chat-role">{msg.role === 'user' ? '🧑 你' : '🤖 AI'}</div>
                    <div className="markdown-content">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                    </div>
                  </div>
                ))
              )}
              {asking && (
                <div className="chat-bubble assistant">
                  <div className="chat-role">🤖 AI</div>
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
