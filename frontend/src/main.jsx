import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

function App() {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [token, setToken] = useState(localStorage.getItem('jarvisToken') || '');
  const [role, setRole] = useState(localStorage.getItem('jarvisRole') || '');
  const [message, setMessage] = useState('How many appointments today?');
  const [chat, setChat] = useState([]);
  const [busy, setBusy] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');

  async function login(event) {
    event.preventDefault();
    setBusy(true);
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (!response.ok) throw new Error('Login failed');
      const data = await response.json();
      localStorage.setItem('jarvisToken', data.access_token);
      localStorage.setItem('jarvisRole', data.role);
      setToken(data.access_token);
      setRole(data.role);
    } catch (error) {
      alert(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function sendMessage(event) {
    event.preventDefault();
    if (!message.trim()) return;
    const userMessage = message;
    setMessage('');
    setChat((items) => [...items, { from: 'user', text: userMessage }]);
    setBusy(true);
    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage }),
      });
      if (!response.ok) throw new Error(await response.text());
      const data = await response.json();
      setChat((items) => [...items, { from: 'assistant', text: data.answer, meta: data.route }]);
    } catch (error) {
      setChat((items) => [...items, { from: 'assistant', text: `Error: ${error.message}`, meta: 'error' }]);
    } finally {
      setBusy(false);
    }
  }

  async function uploadDocument(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    setUploadStatus('Uploading...');
    try {
      const response = await fetch(`${API_BASE_URL}/documents/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!response.ok) throw new Error(await response.text());
      const data = await response.json();
      setUploadStatus(`Indexed ${data.chunks_indexed} chunks from ${data.filename}`);
    } catch (error) {
      setUploadStatus(`Upload failed: ${error.message}`);
    }
  }

  return (
    <main className="app-shell">
      <section className="hero">
        <div>
          <p className="eyebrow">Local-first Clinic AI</p>
          <h1>Jarvis Clinic Assistant</h1>
          <p>Ask live business questions, search patients safely, and query clinic documents using Ollama + RAG.</p>
        </div>
        <span className="role-pill">{token ? `Signed in: ${role}` : 'Not signed in'}</span>
      </section>

      {!token && (
        <form className="card login" onSubmit={login}>
          <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" />
          <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" type="password" />
          <button disabled={busy}>Login</button>
        </form>
      )}

      {token && (
        <>
          <section className="card upload-panel">
            <label>
              Upload clinic document for RAG
              <input type="file" accept=".txt,.md,.pdf" onChange={uploadDocument} />
            </label>
            <span>{uploadStatus}</span>
          </section>

          <section className="card chat-window">
            <div className="messages">
              {chat.map((item, index) => (
                <article key={`${item.from}-${index}`} className={`message ${item.from}`}>
                  <strong>{item.from === 'user' ? 'You' : 'Jarvis'}</strong>
                  <p>{item.text}</p>
                  {item.meta && <small>{item.meta}</small>}
                </article>
              ))}
              {chat.length === 0 && <p className="empty">Try: “Show today’s revenue” or “Search patient named Maria”.</p>}
            </div>
            <form className="composer" onSubmit={sendMessage}>
              <input value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Ask Jarvis..." />
              <button disabled={busy}>Send</button>
            </form>
          </section>
        </>
      )}
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
