import React, { useState, useEffect } from 'react'
import { useAuth } from './auth.jsx'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const AVAILABLE_TOOLS = [
  { id: 'garak', name: 'Garak (NVIDIA)', desc: 'Broad LLM vulnerability probes' },
  { id: 'deepteam', name: 'DeepTeam', desc: 'OWASP Top 10 aligned red teaming' },
  { id: 'pyrit', name: 'PyRIT (Microsoft)', desc: 'Multi-turn attack orchestration' },
  { id: 'promptmap', name: 'Promptmap', desc: 'Prompt injection scanner' },
]

function App() {
  const { authenticated, user, loading, login, logout, getToken } = useAuth()
  const [view, setView] = useState('list') // list | new | detail
  const [jobs, setJobs] = useState([])
  const [selectedJob, setSelectedJob] = useState(null)
  const [report, setReport] = useState(null)
  const [form, setForm] = useState({
    target_name: '',
    type: 'openai',
    model_name: 'gpt-4o-mini',
    base_url: '',
    api_key: '',
    tools: ['garak', 'deepteam'],
    garak_probes: 'encoding,promptinject,dan,lmrc',
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const authHeaders = () => {
    const t = getToken()
    return t ? { Authorization: `Bearer ${t}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' }
  }

  const loadJobs = async () => {
    try {
      const res = await fetch(`${API}/api/v1/scans`, { headers: authHeaders() })
      if (res.ok) {
        const data = await res.json()
        setJobs(data)
      }
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => {
    if (!loading) loadJobs()
    const iv = setInterval(loadJobs, 8000)
    return () => clearInterval(iv)
  }, [loading])

  const createScan = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      const body = {
        target_name: form.target_name,
        target: {
          type: form.type,
          model_name: form.model_name,
          base_url: form.base_url || null,
          api_key: form.api_key || null,
        },
        tools: form.tools,
        options: {
          garak: { probes: form.garak_probes },
          deepteam: { framework: 'OWASPTop10' },
        },
      }
      const res = await fetch(`${API}/api/v1/scans`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const err = await res.text()
        throw new Error(err || res.statusText)
      }
      const job = await res.json()
      setView('list')
      loadJobs()
      setSelectedJob(job)
    } catch (e) {
      setError(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  const openJob = async (job) => {
    setSelectedJob(job)
    setView('detail')
    setReport(null)
    try {
      const res = await fetch(`${API}/api/v1/results/${job.id}/consolidated`, { headers: authHeaders() })
      if (res.ok) setReport(await res.json())
    } catch (e) {
      console.error(e)
    }
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center' }}>
        <p>Loading authentication…</p>
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '1.5rem' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>LLM Security Assessment Platform</h1>
          <p style={{ color: 'var(--muted)', fontSize: '0.9rem' }}>
            Unified red-teaming for Garak · PyRIT · DeepTeam · Promptmap & more
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          {user && <span style={{ color: 'var(--muted)' }}>{user.username}</span>}
          {authenticated ? (
            <button className="secondary" onClick={logout}>Logout</button>
          ) : (
            <button onClick={login}>Login with Keycloak</button>
          )}
        </div>
      </header>

      <nav style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <button className={view === 'list' ? '' : 'secondary'} onClick={() => setView('list')}>Assessments</button>
        <button className={view === 'new' ? '' : 'secondary'} onClick={() => setView('new')}>New Assessment</button>
      </nav>

      {view === 'list' && (
        <div className="card">
          <h2 style={{ marginBottom: '1rem' }}>Recent Assessments</h2>
          {jobs.length === 0 ? (
            <p style={{ color: 'var(--muted)' }}>No assessments yet. Create one to get started.</p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border)' }}>
                  <th style={{ padding: '0.5rem' }}>Target</th>
                  <th>Status</th>
                  <th>Tools</th>
                  <th>Created</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((j) => (
                  <tr key={j.id} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '0.75rem 0.5rem' }}>{j.target_name}</td>
                    <td><span className={`badge ${j.status}`}>{j.status}</span></td>
                    <td style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>{(j.tools_selected || []).join(', ')}</td>
                    <td style={{ fontSize: '0.85rem' }}>{new Date(j.created_at).toLocaleString()}</td>
                    <td><button className="secondary" style={{ padding: '0.3rem 0.7rem' }} onClick={() => openJob(j)}>View</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {view === 'new' && (
        <div className="card">
          <h2 style={{ marginBottom: '1.25rem' }}>New Assessment</h2>
          {error && <p style={{ color: 'var(--danger)', marginBottom: '1rem' }}>{error}</p>}
          <form onSubmit={createScan} style={{ display: 'grid', gap: '1rem' }}>
            <div>
              <label>Target Name *</label>
              <input required value={form.target_name} onChange={(e) => setForm({ ...form, target_name: e.target.value })} placeholder="e.g. Prod GPT-4o endpoint" />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label>Target Type</label>
                <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
                  <option value="openai">OpenAI / Compatible</option>
                  <option value="azure_openai">Azure OpenAI</option>
                  <option value="ollama">Ollama</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="custom_rest">Custom REST</option>
                </select>
              </div>
              <div>
                <label>Model Name</label>
                <input value={form.model_name} onChange={(e) => setForm({ ...form, model_name: e.target.value })} />
              </div>
            </div>
            <div>
              <label>Base URL (optional)</label>
              <input value={form.base_url} onChange={(e) => setForm({ ...form, base_url: e.target.value })} placeholder="https://api.openai.com/v1 or http://ollama:11434/v1" />
            </div>
            <div>
              <label>API Key (optional – can also be set in env)</label>
              <input type="password" value={form.api_key} onChange={(e) => setForm({ ...form, api_key: e.target.value })} />
            </div>
            <div>
              <label>Tools to run</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', marginTop: '0.4rem' }}>
                {AVAILABLE_TOOLS.map((t) => (
                  <label key={t.id} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', background: 'var(--bg)', padding: '0.4rem 0.7rem', borderRadius: 6, border: '1px solid var(--border)' }}>
                    <input
                      type="checkbox"
                      checked={form.tools.includes(t.id)}
                      onChange={(e) => {
                        if (e.target.checked) setForm({ ...form, tools: [...form.tools, t.id] })
                        else setForm({ ...form, tools: form.tools.filter((x) => x !== t.id) })
                      }}
                    />
                    <span>{t.name}</span>
                  </label>
                ))}
              </div>
            </div>
            {form.tools.includes('garak') && (
              <div>
                <label>Garak probes (comma-separated)</label>
                <input value={form.garak_probes} onChange={(e) => setForm({ ...form, garak_probes: e.target.value })} />
              </div>
            )}
            <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
              <button type="submit" disabled={submitting || form.tools.length === 0}>
                {submitting ? 'Launching…' : 'Launch Assessment'}
              </button>
              <button type="button" className="secondary" onClick={() => setView('list')}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {view === 'detail' && selectedJob && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <h2>{selectedJob.target_name}</h2>
            <button className="secondary" onClick={() => setView('list')}>Back</button>
          </div>
          <p style={{ marginBottom: '0.5rem' }}>
            Status: <span className={`badge ${selectedJob.status}`}>{selectedJob.status}</span>
          </p>
          <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
            Tools: {(selectedJob.tools_selected || []).join(', ')} · Created {new Date(selectedJob.created_at).toLocaleString()}
          </p>

          {report ? (
            <div>
              <h3 style={{ marginBottom: '0.75rem' }}>Consolidated Report</h3>
              <p style={{ marginBottom: '0.5rem' }}>
                Overall Risk: <strong style={{ color: report.overall_risk === 'high' ? 'var(--danger)' : report.overall_risk === 'medium' ? 'var(--warning)' : 'var(--success)' }}>
                  {report.overall_risk?.toUpperCase()}
                </strong>
              </p>
              <p style={{ marginBottom: '1rem' }}>{report.summary}</p>
              <h4 style={{ marginBottom: '0.5rem' }}>Recommendations</h4>
              <ul style={{ marginBottom: '1.5rem', paddingLeft: '1.25rem' }}>
                {(report.recommendations || []).map((r, i) => <li key={i}>{r}</li>)}
              </ul>
              <h4 style={{ marginBottom: '0.5rem' }}>Per-tool Results</h4>
              {Object.entries(report.tool_results || {}).map(([tool, data]) => (
                <div key={tool} style={{ background: 'var(--bg)', padding: '0.75rem', borderRadius: 6, marginBottom: '0.5rem' }}>
                  <strong>{tool}</strong> – <span className={`badge ${data.status}`}>{data.status}</span>
                  <pre style={{ fontSize: '0.8rem', marginTop: '0.4rem', whiteSpace: 'pre-wrap', color: 'var(--muted)' }}>
                    {JSON.stringify(data.summary, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: 'var(--muted)' }}>
              {selectedJob.status === 'running' || selectedJob.status === 'pending'
                ? 'Assessment still in progress… refresh in a few seconds.'
                : 'No consolidated report available yet.'}
            </p>
          )}
        </div>
      )}
    </div>
  )
}

export default App
