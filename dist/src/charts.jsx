// Dependency-free SVG charts.
export const SEV = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MEDIUM: '#eab308',
  LOW: '#3b82f6',
  SAFE: '#22c55e',
}

const nf = (n) => (n == null ? '—' : Number(n).toLocaleString())

export function Donut({ data = {} }) {
  const order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'SAFE']
  const total = order.reduce((s, k) => s + (data[k] || 0), 0) || 1
  const R = 54
  const C = 2 * Math.PI * R
  let off = 0
  const segs = []
  order.forEach((k) => {
    const v = data[k] || 0
    if (!v) return
    const len = (v / total) * C
    segs.push(
      <circle
        key={k}
        r={R}
        cx="70"
        cy="70"
        fill="none"
        stroke={SEV[k]}
        strokeWidth="18"
        strokeDasharray={`${len} ${C - len}`}
        strokeDashoffset={-off}
        transform="rotate(-90 70 70)"
      />
    )
    off += len
  })
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
      <svg width="140" height="140" viewBox="0 0 140 140">
        {segs}
        <text x="70" y="66" textAnchor="middle" fill="#e6e9f2" fontSize="22" fontWeight="700">
          {nf(total)}
        </text>
        <text x="70" y="86" textAnchor="middle" fill="#8b93a7" fontSize="11">
          scans
        </text>
      </svg>
      <div className="legend" style={{ flexDirection: 'column', gap: 8 }}>
        {order
          .filter((k) => data[k])
          .map((k) => (
            <div key={k}>
              <i style={{ background: SEV[k] }} />
              {k} · <b>{nf(data[k])}</b>
            </div>
          ))}
      </div>
    </div>
  )
}

export function AreaChart({ series = [] }) {
  const W = 560
  const H = 190
  const pad = 28
  if (!series.length) return <div className="empty">No data yet</div>
  const max = Math.max(1, ...series.map((d) => d.total))
  const x = (i) => pad + i * ((W - 2 * pad) / Math.max(1, series.length - 1))
  const y = (v) => H - pad - (v / max) * (H - 2 * pad)
  const line = (key) =>
    series.map((d, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(d[key]).toFixed(1)}`).join(' ')
  const area = `${line('total')} L${x(series.length - 1)},${H - pad} L${x(0)},${H - pad} Z`
  const step = Math.ceil(series.length / 6)
  return (
    <>
      <svg width="100%" viewBox={`0 0 ${W} ${H}`}>
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="rgba(99,102,241,.5)" />
            <stop offset="1" stopColor="rgba(99,102,241,0)" />
          </linearGradient>
        </defs>
        {[0, 0.5, 1].map((f) => (
          <line
            key={f}
            x1={pad}
            x2={W - pad}
            y1={pad + f * (H - 2 * pad)}
            y2={pad + f * (H - 2 * pad)}
            stroke="rgba(255,255,255,.06)"
          />
        ))}
        <path d={area} fill="url(#g)" />
        <path d={line('total')} fill="none" stroke="#818cf8" strokeWidth="2.5" />
        <path d={line('blocked')} fill="none" stroke="#ef4444" strokeWidth="2.5" strokeDasharray="4 3" />
        {series.map((d, i) =>
          i % step === 0 ? (
            <text key={i} x={x(i)} y={H - 8} fill="#8b93a7" fontSize="9" textAnchor="middle">
              {d.day.slice(5)}
            </text>
          ) : null
        )}
      </svg>
      <div className="legend">
        <span>
          <i style={{ background: '#818cf8' }} />
          Total scans
        </span>
        <span>
          <i style={{ background: '#ef4444' }} />
          Blocked
        </span>
      </div>
    </>
  )
}

export function HBars({ data = [], color }) {
  const max = Math.max(1, ...data.map((d) => d[1]))
  if (!data.length) return <div className="empty">No data yet</div>
  return (
    <div>
      {data.map(([name, val]) => (
        <div className="bar-row" key={name}>
          <div className="name" title={name}>
            {name}
          </div>
          <div className="bar-track">
            <div
              className="bar-fill"
              style={{ width: `${((val / max) * 100).toFixed(0)}%`, background: color ? color(name) : undefined }}
            />
          </div>
          <div className="val">{nf(val)}</div>
        </div>
      ))}
    </div>
  )
}
