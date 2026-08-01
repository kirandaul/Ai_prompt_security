import { useEffect, useState, useCallback } from 'react'
import * as API from './api.js'
import { Donut, AreaChart, HBars } from './charts.jsx'

const nf = (n) => (n == null ? '—' : Number(n).toLocaleString())
const EMPTY_FILTERS = { severity: '', source: '', client_id: '', date_from: '', date_to: '', search: '', scan_type: '' }

export default function App() {
  const [user, setUser] = useState(null)
  const [booting, setBooting] = useState(true)

  useEffect(() => {
    API.getMe().then((me) => {
      setUser(me?.user || null)
      setBooting(false)
    })
  }, [])

  if (booting) return <div className="boot">Loading…</div>
  if (!user) return <Login onLogin={setUser} />
  return <Dashboard user={user} onLogout={() => setUser(null)} />
}

function Login({ onLogin }) {
  const [u, setU] = useState('')
  const [p, setP] = useState('')
  const [err, setErr] = useState('')
  const submit = async () => {
    setErr('')
    try {
      const d = await API.login(u, p)
      onLogin(d.user)
    } catch {
      setErr('Invalid username or password.')
    }
  }
  return (
    <div className="overlay">
      <div className="login">
        <img src="/cybage_logo1.webp" alt="Cybage" className="logo" />
        <h2>Cybage Browser Prompt Detection</h2>
        <p>Security Console — Admin sign in</p>
        <div className="fld">
          <input type="text" value={u} onChange={(e) => setU(e.target.value)}
                 onKeyDown={(e) => e.key === 'Enter' && submit()}
                 placeholder="Username" autoComplete="username" />
        </div>
        <div className="fld">
          <input
            type="password"
            value={p}
            onChange={(e) => setP(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && submit()}
            placeholder="Password"
            autoComplete="current-password"
          />
        </div>
        <button className="btn primary" onClick={submit}>Sign in</button>
        <div className="err">{err}</div>
        <div className="hint">Default: <b>admin / admin123</b> — change via env vars.</div>
      </div>
    </div>
  )
}

function Dashboard({ user, onLogout }) {
  const [data, setData] = useState(null)
  const [logs, setLogs] = useState({ logs: [], total: 0 })
  const [bench, setBench] = useState(null)
  const [filters, setFilters] = useState(EMPTY_FILTERS)
  const [updated, setUpdated] = useState('')

  const loadLogs = useCallback(async (f) => {
    try {
      setLogs(await API.getLogs(f))
    } catch {
      onLogout()
    }
  }, [onLogout])

  const loadAll = useCallback(async () => {
    try {
      const d = await API.getOverview()
      setData(d)
      setUpdated(new Date().toLocaleTimeString())
      API.getBenchmark().then(setBench).catch(() => {})
      await loadLogs(filters)
    } catch {
      onLogout()
    }
  }, [filters, loadLogs, onLogout])

  useEffect(() => {
    loadAll()
    // Refresh often so the newest prompts appear almost live.
    const t = setInterval(loadAll, 8000)
    return () => clearInterval(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const logout = async () => {
    await API.logout()
    onLogout()
  }

  const o = data?.overview || {}
  const rate = o.total_scans ? Math.round((o.threats_blocked / o.total_scans) * 100) : 0

  return (
    <div className="wrap">
      <div className="top">
        <div className="brand">
          <img src="/cybage_logo1.webp" alt="Cybage" className="logo" />
          <div>
            <h1>Cybage Browser Prompt Detection <span className="pill">LIVE</span></h1>
            <p>AI Data-Loss Prevention · Security Console</p>
          </div>
        </div>
        <div className="userbox">
          {updated && <span className="refresh-note">Updated {updated}</span>}
          <span>👤 {user}</span>
          <button className="btn" onClick={loadAll}>↻ Refresh</button>
          <button className="btn" onClick={logout}>Logout</button>
        </div>
      </div>

      <div className="grid cards">
        <StatCard hero label="🔒 Secrets Protected" num={nf(o.secrets_protected)} sub="to date" />
        <StatCard label="Threats Blocked" num={nf(o.threats_blocked)} sub={`${rate}% of prompts blocked`} />
        <StatCard label="Total Prompts Scanned" num={nf(o.total_scans)} sub="across all users" />
        <StatCard label="Items Flagged" num={nf(o.items_flagged)} sub="findings detected" />
        <StatCard label="Active Clients" num={nf(o.active_clients)} sub="browser installs" />
      </div>

      <div className="grid panels">
        <div className="card">
          <h3>Scan Activity <span>· last 14 days (blocked vs total)</span></h3>
          <AreaChart series={data?.timeseries || []} />
        </div>
        <div className="card">
          <h3>Severity Mix</h3>
          <Donut data={data?.severity || {}} />
        </div>
      </div>

      <div className="grid panels2">
        <div className="card">
          <h3>Threats by Category</h3>
          <HBars data={Object.entries(data?.categories || {})} />
        </div>
        <div className="card">
          <h3>Top Clients <span>· by blocks</span></h3>
          <HBars data={(data?.top_clients || []).map((c) => [c.hostname || 'unknown', c.blocked])} />
        </div>
      </div>

      <Accuracy bench={bench} />

      <ActivationKeysPanel />

      <Filters filters={filters} setFilters={setFilters} onApply={() => loadLogs(filters)}
               onReset={() => { setFilters(EMPTY_FILTERS); loadLogs(EMPTY_FILTERS) }} />

      <LogsTable logs={logs.logs} />
    </div>
  )
}

function Accuracy({ bench }) {
  if (!bench) return null
  const run = bench.run
  if (!run) {
    return (
      <div className="card" style={{ marginTop: 16 }}>
        <h3>Detection Accuracy</h3>
        <div className="empty">
          No benchmark run yet — run <code>python benchmark.py</code> in <code>backend/</code>.
        </div>
      </div>
    )
  }
  const pct = (v) => `${(v * 100).toFixed(1)}%`
  const wrong = bench.wrong || []
  return (
    <div style={{ marginTop: 16 }}>
      <div className="card">
        <h3>
          Detection Accuracy <span>· {run.total} test cases · {run.duration_ms} ms
          · {run.created_at?.replace('T', ' ').replace('+00:00', '')}</span>
        </h3>

        <div className="grid cards" style={{ marginBottom: 16 }}>
          <div className="card stat"><div className="label">Accuracy</div><div className="num">{pct(run.accuracy)}</div><div className="sub">overall correct</div></div>
          <div className="card stat"><div className="label">Precision</div><div className="num">{pct(run.precision)}</div><div className="sub">of flags, truly bad</div></div>
          <div className="card stat"><div className="label">Recall</div><div className="num">{pct(run.recall)}</div><div className="sub">of leaks, caught</div></div>
          <div className="card stat"><div className="label">F1 Score</div><div className="num">{pct(run.f1)}</div><div className="sub">balance</div></div>
          <div className="card stat"><div className="label">Wrong Cases</div><div className="num">{run.fp + run.fn}</div><div className="sub">{run.fp} false alarm · {run.fn} missed</div></div>
        </div>

        <div className="legend" style={{ marginTop: 0 }}>
          <span className="badge sev-SAFE">✔ {run.tp} correctly blocked</span>
          <span className="badge sev-LOW">✔ {run.tn} correctly allowed</span>
          <span className="badge sev-MEDIUM">⚠ {run.fp} false positives</span>
          <span className="badge sev-CRITICAL">✖ {run.fn} false negatives (missed)</span>
        </div>
      </div>


    </div>
  )
}

function StatCard({ label, num, sub, hero }) {
  return (
    <div className={'card stat' + (hero ? ' hero' : '')}>
      <div className="label">{label}</div>
      <div className="num">{num}</div>
      <div className="sub">{sub}</div>
    </div>
  )
}

function Filters({ filters, setFilters, onApply, onReset }) {
  const set = (k) => (e) => setFilters({ ...filters, [k]: e.target.value })
  return (
    <div className="filters">
      <Field label="Scan Type">
        <select value={filters.scan_type} onChange={set('scan_type')}>
          <option value="">All</option>
          <option>text</option>
          <option>image</option>
          <option>document</option>
        </select>
      </Field>
      <Field label="Severity">
        <select value={filters.severity} onChange={set('severity')}>
          <option value="">All</option>
          {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'SAFE'].map((s) => <option key={s}>{s}</option>)}
        </select>
      </Field>
      <Field label="Source">
        <select value={filters.source} onChange={set('source')}>
          <option value="">All</option>
          <option>chatgpt.com</option>
          <option>claude.ai</option>
        </select>
      </Field>
      <Field label="Client ID"><input value={filters.client_id} onChange={set('client_id')} placeholder="client id" /></Field>
      <Field label="From"><input type="date" value={filters.date_from} onChange={set('date_from')} /></Field>
      <Field label="To"><input type="date" value={filters.date_to} onChange={set('date_to')} /></Field>
      <Field label="Search prompt"><input value={filters.search} onChange={set('search')} placeholder="text…" /></Field>
      <button className="btn primary" onClick={onApply}>Apply</button>
      <button className="btn" onClick={onReset}>Reset</button>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <div className="f">
      <label>{label}</label>
      {children}
    </div>
  )
}

function ActivationKeysPanel() {
  const [keys, setKeys] = useState([])
  const [loading, setLoading] = useState(false)
  const [hostname, setHostname] = useState('')
  const [copiedKey, setCopiedKey] = useState(null)
  const [usagePopup, setUsagePopup] = useState(null)
  const [usageLoading, setUsageLoading] = useState(false)

  // Load keys when component mounts
  useEffect(() => {
    loadKeys()
  }, [])

  const loadKeys = async () => {
    setLoading(true)
    try {
      const r = await fetch('/api/admin/activation-keys')
      const data = await r.json()
      setKeys(data.keys || [])
    } catch (e) {
      console.error('Failed to load keys:', e)
    }
    setLoading(false)
  }

  const copyToClipboard = (key) => {
    navigator.clipboard.writeText(key).then(() => {
      setCopiedKey(key)
      setTimeout(() => setCopiedKey(null), 2000)
    })
  }

  const showKeyUsage = async (key) => {
    setUsageLoading(true)
    try {
      const r = await fetch(`/api/admin/key-usage/${encodeURIComponent(key)}`)
      const data = await r.json()
      if (data.status === 'success') {
        setUsagePopup(data.usage)
      } else {
        alert(`❌ Error: ${data.message}`)
      }
    } catch (e) {
      alert(`❌ Failed: ${e.message}`)
    }
    setUsageLoading(false)
  }

  const generateKey = async () => {
    try {
      const r = await fetch('/api/admin/generate-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hostname: hostname || 'extension' })
      })
      const data = await r.json()
      if (data.status === 'success') {
        const message = `✅ Key Generated!\n\nKey:\n${data.key}\n\nExtension ID:\n${data.extension_id}\n\nClick OK to copy key to clipboard.`
        alert(message)
        copyToClipboard(data.key)
        setHostname('')
        loadKeys()
      } else {
        alert(`❌ Error: ${data.message}`)
      }
    } catch (e) {
      alert(`❌ Failed: ${e.message}`)
    }
  }

  const toggleKey = async (key, isActive) => {
    try {
      const endpoint = isActive ? '/api/admin/deactivate-key' : '/api/admin/activate-key'
      const r = await fetch(endpoint + `?key=${encodeURIComponent(key)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      const data = await r.json()
      if (data.status === 'success') {
        loadKeys()
      } else {
        alert(`❌ Error: ${data.message}`)
      }
    } catch (e) {
      alert(`❌ Failed: ${e.message}`)
    }
  }

  const deleteKey = async (key) => {
    if (!confirm(`Delete key ${key.substring(0, 16)}...?`)) return
    try {
      const r = await fetch(`/api/admin/delete-key?key=${encodeURIComponent(key)}`, {
        method: 'DELETE'
      })
      const data = await r.json()
      if (data.status === 'success') {
        loadKeys()
      } else {
        alert(`❌ Error: ${data.message}`)
      }
    } catch (e) {
      alert(`❌ Failed: ${e.message}`)
    }
  }

  return (
    <div className="card" style={{ marginTop: 16 }}>
      <h3>🔑 Extension Activation Keys</h3>
      
      <div style={{ display: 'flex', gap: 10, marginBottom: 16 }}>
        <input 
          type="text"
          placeholder="Hostname (optional)"
          value={hostname}
          onChange={(e) => setHostname(e.target.value)}
          style={{ flex: 1 }}
        />
        <button className="btn primary" onClick={generateKey}>+ Generate Key</button>
        <button className="btn" onClick={loadKeys}>{loading ? '...' : '↻ Refresh'}</button>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ minWidth: '1200px' }}>
          <thead>
            <tr>
              <th>Status</th><th>Key (Click to Copy)</th><th>Extension ID</th><th>Hostname</th>
              <th>Created</th><th>Last Used</th><th>User Agent</th><th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {keys.map((k) => (
              <tr key={k.id}>
                <td><span className="type-badge">{k.status}</span></td>
                <td 
                  className="mono" 
                  title={k.key}
                  onClick={() => copyToClipboard(k.key)}
                  style={{ 
                    cursor: 'pointer', 
                    padding: '8px 12px',
                    backgroundColor: copiedKey === k.key ? '#dcfce7' : 'transparent',
                    borderRadius: '4px',
                    transition: 'background-color 0.2s'
                  }}
                >
                  {copiedKey === k.key ? '✅ Copied!' : k.key_short}
                </td>
                <td className="mono">{k.extension_id || '—'}</td>
                <td>{k.hostname || '—'}</td>
                <td>{(k.created_at || '').replace('T', ' ').substring(0, 16)}</td>
                <td>{k.last_used ? (k.last_used || '').replace('T', ' ').substring(0, 16) : '—'}</td>
                <td style={{ fontSize: '11px' }}>{k.user_agent}</td>
                <td>
                  <button 
                    className="btn" 
                    style={{ padding: '4px 8px', fontSize: '12px', marginRight: '4px' }}
                    onClick={() => showKeyUsage(k.key)}
                    title="View which devices used this key"
                  >
                    📊 Usage
                  </button>
                  <button 
                    className="btn" 
                    style={{ padding: '4px 8px', fontSize: '12px', marginRight: '4px' }}
                    onClick={() => toggleKey(k.key, k.is_active)}
                  >
                    {k.is_active ? '🔴 Deactivate' : '🟢 Activate'}
                  </button>
                  <button 
                    className="btn" 
                    style={{ padding: '4px 8px', fontSize: '12px', color: '#dc2626' }}
                    onClick={() => deleteKey(k.key)}
                  >
                    🗑 Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {keys.length === 0 && <div className="empty">No activation keys. Click "Generate Key" to create one.</div>}
      
      <div style={{ marginTop: 12, fontSize: '12px', color: '#64748b' }}>
        📊 Total: {keys.length} key(s) | 🟢 Active: {keys.filter(k => k.is_active).length} | 🔴 Inactive: {keys.filter(k => !k.is_active).length}
      </div>

      {usagePopup && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0,
          width: '100%', height: '100%',
          background: 'rgba(0,0,0,0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999
        }}>
          <div style={{
            background: 'white',
            borderRadius: '12px',
            padding: '24px',
            maxWidth: '500px',
            maxHeight: '80vh',
            overflowY: 'auto'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ margin: 0 }}>📊 Key Usage</h3>
              <button 
                onClick={() => setUsagePopup(null)}
                style={{ background: 'none', border: 'none', fontSize: '24px', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <div style={{ marginBottom: '16px', padding: '12px', background: '#f0f4f8', borderRadius: '8px' }}>
              <div><strong>Key:</strong> {usagePopup.key}</div>
              <div><strong>Total Requests:</strong> {usagePopup.total_requests}</div>
              <div><strong>First Used:</strong> {(usagePopup.first_used || '').replace('T', ' ').substring(0, 19)}</div>
              <div><strong>Last Used:</strong> {usagePopup.last_used ? (usagePopup.last_used || '').replace('T', ' ').substring(0, 19) : '—'}</div>
            </div>

            <h4>Devices Using This Key:</h4>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #e2e8f0' }}>
                  <th style={{ textAlign: 'left', padding: '8px', paddingBottom: '12px' }}>Hostname</th>
                  <th style={{ textAlign: 'right', padding: '8px', paddingBottom: '12px' }}>Requests</th>
                  <th style={{ textAlign: 'left', padding: '8px', paddingBottom: '12px' }}>Last Used</th>
                </tr>
              </thead>
              <tbody>
                {usagePopup.hostnames && usagePopup.hostnames.length > 0 ? (
                  usagePopup.hostnames.map((h, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #e2e8f0' }}>
                      <td style={{ padding: '8px' }}><strong>{h.hostname}</strong></td>
                      <td style={{ padding: '8px', textAlign: 'right' }}>{h.count}</td>
                      <td style={{ padding: '8px', fontSize: '12px', color: '#64748b' }}>
                        {(h.last_used || '').replace('T', ' ').substring(0, 19)}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="3" style={{ padding: '12px', textAlign: 'center', color: '#94a3b8' }}>
                      No usage data yet
                    </td>
                  </tr>
                )}
              </tbody>
            </table>

            <button 
              className="btn primary"
              onClick={() => setUsagePopup(null)}
              style={{ marginTop: '16px', width: '100%' }}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function LogsTable({ logs }) {
  return (
    <div className="card" style={{ padding: '6px 6px 2px', overflowX: 'auto' }}>
      <table style={{ minWidth: '1200px' }}>
        <thead>
          <tr>
            <th>Time (UTC)</th><th>Type</th><th>API Key</th><th>Hostname / IP</th><th>Source</th><th>Severity</th>
            <th>Findings</th><th>Categories</th><th>Redacted Prompt</th><th>Action</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((L) => (
            <tr key={L.id}>
              <td style={{ minWidth: '160px' }}>{(L.created_at || '').replace('T', ' ').replace('+00:00', '')}</td>
              <td style={{ minWidth: '70px' }}><span className="type-badge">{L.scan_type || 'text'}</span></td>
              <td style={{ minWidth: '100px' }} className="mono" title={L.activation_key || ''}>{L.activation_key ? L.activation_key.substring(0, 8) + '...' + L.activation_key.substring(L.activation_key.length - 4) : '—'}</td>
              <td style={{ minWidth: '180px' }} className="mono" title={L.user_agent || ''}>
                <div>{L.hostname || '—'}</div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>{L.ip || '—'}</div>
              </td>
              <td style={{ minWidth: '120px' }}>{L.source || '—'}</td>
              <td style={{ minWidth: '90px' }}><span className={'badge sev-' + L.severity}>{L.severity}</span></td>
              <td style={{ minWidth: '70px', textAlign: 'center' }}><strong>{L.findings_count || 0}</strong></td>
              <td style={{ minWidth: '150px' }}>{(L.categories || []).map((c) => <span className="cat" key={c}>{c}</span>)}{(L.categories || []).length === 0 && '—'}</td>
              <td style={{ minWidth: '200px' }} className="mono" title={L.redacted_prompt || ''}>{L.redacted_prompt || '—'}</td>
              <td style={{ minWidth: '80px' }}>{L.allow_send ? '✅ Allowed' : '⛔ Blocked'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {logs.length === 0 && <div className="empty">No events match your filters.</div>}
    </div>
  )
}
