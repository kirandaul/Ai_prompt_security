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
          <HBars data={(data?.top_clients || []).map((c) => [c.client_id.slice(0, 16), c.blocked])} />
        </div>
      </div>

      <Accuracy bench={bench} />

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

      {wrong.length > 0 && (
        <div className="card" style={{ padding: '6px 6px 2px', marginTop: 16 }}>
          <table>
            <thead>
              <tr><th>Outcome</th><th>Category</th><th>Test prompt</th><th>Detected as</th><th>Risk</th></tr>
            </thead>
            <tbody>
              {wrong.map((c) => (
                <tr key={c.id}>
                  <td>
                    <span className={'badge ' + (c.outcome === 'FN' ? 'sev-CRITICAL' : 'sev-MEDIUM')}>
                      {c.outcome === 'FN' ? 'MISSED' : 'FALSE ALARM'}
                    </span>
                  </td>
                  <td className="mono">{c.category}</td>
                  <td className="mono" title={c.prompt}>{c.prompt}</td>
                  <td>{(c.findings || []).join(', ') || '—'}</td>
                  <td>{c.risk_score}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
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

function LogsTable({ logs }) {
  return (
    <div className="card" style={{ padding: '6px 6px 2px' }}>
      <table>
        <thead>
          <tr>
            <th>Time (UTC)</th><th>Type</th><th>Client</th><th>Host / IP</th><th>Source</th><th>Severity</th>
            <th>Categories</th><th>Redacted Prompt</th><th>Action</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((L) => (
            <tr key={L.id}>
              <td>{(L.created_at || '').replace('T', ' ').replace('+00:00', '')}</td>
              <td><span className="type-badge">{L.scan_type || 'text'}</span></td>
              <td className="mono">{L.client_id || '—'}</td>
              <td className="mono" title={L.user_agent || ''}>{L.ip || '—'}</td>
              <td>{L.source || '—'}</td>
              <td><span className={'badge sev-' + L.severity}>{L.severity}</span></td>
              <td>{(L.categories || []).map((c) => <span className="cat" key={c}>{c}</span>)}{(L.categories || []).length === 0 && '—'}</td>
              <td className="mono" title={L.redacted_prompt || ''}>{L.redacted_prompt || '—'}</td>
              <td>{L.allow_send ? '✅ Allowed' : '⛔ Blocked'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {logs.length === 0 && <div className="empty">No events match your filters.</div>}
    </div>
  )
}
