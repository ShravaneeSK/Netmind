import { useCallback, useEffect, useRef, useState } from 'react'

const API = 'http://127.0.0.1:8000'
const POLL_MS = 5000

const FAULTS = [
  'normal',
  'weak_signal',
  'congestion',
  'dns_failure',
  'gateway_failure',
  'internet_failure',
  'device_overload',
  'intermittent_loss',
  'dhcp_failure',
]

const SEVERITY_STYLE = {
  None: 'bg-emerald-600',
  Low: 'bg-sky-600',
  Medium: 'bg-amber-600',
  High: 'bg-orange-600',
  Critical: 'bg-rose-600',
}

function fmt(value, unit = '') {
  if (value === null || value === undefined) return '-'
  if (value === -1) return 'failed'
  const n = Number(value)
  const shown = Number.isInteger(n) ? n : n.toFixed(1)
  return `${shown}${unit}`
}

function Card({ label, value }) {
  return (
    <div className="rounded-lg bg-slate-800 p-4">
      <div className="text-xs uppercase tracking-wide text-slate-400">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{value}</div>
    </div>
  )
}

function SeverityBadge({ severity }) {
  return (
    <span className={`rounded px-2 py-0.5 text-sm ${SEVERITY_STYLE[severity] ?? 'bg-slate-600'}`}>
      {severity}
    </span>
  )
}

export default function App() {
  const [view, setView] = useState('live')
  const [latest, setLatest] = useState(null)
  const [rows, setRows] = useState([])
  const [history, setHistory] = useState([])
  const [error, setError] = useState(null)
  const [updated, setUpdated] = useState(null)

  const [selected, setSelected] = useState(null)
  const [diag, setDiag] = useState(null)
  const [diagLoading, setDiagLoading] = useState(false)
  const [diagError, setDiagError] = useState(null)
  const [demoBusy, setDemoBusy] = useState(null)
  const requestCounter = useRef(0)

  const load = useCallback(async () => {
    try {
      const [l, m] = await Promise.all([
        fetch(`${API}/latest`),
        fetch(`${API}/merged?limit=15`),
      ])
      if (l.status === 404) setLatest(null)
      else if (l.ok) setLatest(await l.json())
      else throw new Error(`latest: HTTP ${l.status}`)
      if (!m.ok) throw new Error(`merged: HTTP ${m.status}`)
      setRows(await m.json())
      setError(null)
      setUpdated(new Date())
    } catch (e) {
      setError(e.message === 'Failed to fetch' ? 'Backend not reachable' : e.message)
    }
  }, [])

  const loadHistory = useCallback(async () => {
    try {
      const r = await fetch(`${API}/diagnoses?limit=50`)
      if (!r.ok) throw new Error(`diagnoses: HTTP ${r.status}`)
      setHistory(await r.json())
    } catch (e) {
      setError(e.message === 'Failed to fetch' ? 'Backend not reachable' : e.message)
    }
  }, [])

  useEffect(() => {
    load()
    const timer = setInterval(load, POLL_MS)
    return () => clearInterval(timer)
  }, [load])

  useEffect(() => {
    if (view !== 'history') return undefined
    loadHistory()
    const timer = setInterval(loadHistory, POLL_MS)
    return () => clearInterval(timer)
  }, [view, loadHistory])

  const diagnose = useCallback(async (id) => {
    const mine = ++requestCounter.current
    setSelected(id)
    setDiag(null)
    setDiagError(null)
    setDiagLoading(true)
    try {
      const r = await fetch(`${API}/diagnose/${id}`, { method: 'POST' })
      if (!r.ok) {
        const body = await r.json().catch(() => ({}))
        throw new Error(body.detail ?? `HTTP ${r.status}`)
      }
      const data = await r.json()
      if (mine === requestCounter.current) setDiag(data)
    } catch (e) {
      if (mine === requestCounter.current) {
        setDiagError(e.message === 'Failed to fetch' ? 'Backend not reachable' : e.message)
      }
    } finally {
      if (mine === requestCounter.current) setDiagLoading(false)
    }
  }, [])

  const showStored = (item) => {
    requestCounter.current += 1
    setSelected(item.telemetry_id)
    setDiagError(null)
    setDiagLoading(false)
    setDiag({ ...item, sources: [], stored: true })
  }

  const runDemo = async (fault) => {
    setDemoBusy(fault)
    try {
      const r = await fetch(`${API}/demo/${fault}`, { method: 'POST' })
      if (!r.ok) {
        const body = await r.json().catch(() => ({}))
        throw new Error(body.detail ?? `HTTP ${r.status}`)
      }
      const data = await r.json()
      await load()
      await diagnose(data.telemetry_id)
      if (view === 'history') await loadHistory()
    } catch (e) {
      setSelected(null)
      setDiag(null)
      setDiagError(e.message === 'Failed to fetch' ? 'Backend not reachable' : e.message)
    } finally {
      setDemoBusy(null)
    }
  }

  const pred = latest?.prediction
  const rec = latest?.record

  return (
    <div className="min-h-screen bg-slate-900 p-6 text-slate-100">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">NetMind</h1>
          <p className="text-slate-400">Network monitoring dashboard</p>
        </div>
        <span className={`rounded px-3 py-1 text-sm ${error ? 'bg-rose-600' : 'bg-emerald-600'}`}>
          {error ?? `Live, updated ${updated ? updated.toLocaleTimeString() : '...'}`}
        </span>
      </header>

      <nav className="mt-4 flex gap-2">
        {['live', 'history'].map((v) => (
          <button
            key={v}
            onClick={() => setView(v)}
            className={`rounded px-4 py-1 text-sm capitalize ${
              view === v ? 'bg-sky-600' : 'bg-slate-800 hover:bg-slate-700'
            }`}
          >
            {v}
          </button>
        ))}
      </nav>

      <section className="mt-4 rounded-lg bg-slate-800 p-3">
        <div className="text-xs uppercase tracking-wide text-slate-400">
          Demo: inject one simulated fault (not real measurements)
        </div>
        <div className="mt-2 flex flex-wrap gap-2">
          {FAULTS.map((f) => (
            <button
              key={f}
              disabled={demoBusy !== null}
              onClick={() => runDemo(f)}
              className="rounded bg-slate-700 px-2 py-1 text-xs hover:bg-slate-600 disabled:opacity-50"
            >
              {demoBusy === f ? 'working...' : f.replaceAll('_', ' ')}
            </button>
          ))}
        </div>
      </section>

      {view === 'live' && !rec && !error && (
        <p className="mt-8 text-slate-400">No readings yet. Run the simulator or the ESP32 node.</p>
      )}

      {view === 'live' && rec && (
        <section className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
          <div className="col-span-2 rounded-lg bg-slate-800 p-4">
            <div className="text-xs uppercase tracking-wide text-slate-400">Current state</div>
            {pred ? (
              <>
                <div className="mt-1 flex items-center gap-3">
                  <span className="text-2xl font-semibold">{pred.fault_label.replaceAll('_', ' ')}</span>
                  <SeverityBadge severity={pred.severity} />
                </div>
                <div className="mt-1 text-xs text-slate-400">
                  Confidence {Math.round(pred.confidence * 100)}%
                  {pred.is_anomaly ? ' - unusual compared with normal behaviour' : ''}
                </div>
                <button
                  onClick={() => diagnose(rec.id)}
                  className="mt-3 rounded bg-sky-600 px-3 py-1 text-sm hover:bg-sky-500"
                >
                  Explain current reading
                </button>
              </>
            ) : (
              <div className="mt-1 text-slate-400">{latest?.note ?? 'No prediction'}</div>
            )}
          </div>
          <Card label="Signal" value={fmt(rec.rssi, ' dBm')} />
          <Card label="Gateway latency" value={fmt(rec.gateway_latency, ' ms')} />
          <Card label="Internet latency" value={fmt(rec.internet_latency, ' ms')} />
          <Card label="DNS time" value={fmt(rec.dns_time, ' ms')} />
          <Card label="Packet loss" value={fmt(rec.packet_loss, ' %')} />
          <Card label="Free memory" value={fmt(rec.free_heap, ' B')} />
        </section>
      )}

      <div className="mt-8 grid gap-6 lg:grid-cols-3">
        <section className="lg:col-span-2">
          {view === 'live' ? (
            <>
              <h2 className="mb-2 text-lg font-semibold">Recent readings</h2>
              <div className="overflow-x-auto rounded-lg bg-slate-800">
                <table className="w-full text-left text-sm">
                  <thead className="text-xs uppercase text-slate-400">
                    <tr>
                      {['Time', 'ID', 'Device', 'Signal', 'Gateway', 'Internet', 'DNS', 'Loss', 'Packets'].map((h) => (
                        <th key={h} className="px-3 py-2">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((r) => (
                      <tr
                        key={r.id}
                        onClick={() => diagnose(r.id)}
                        className={`cursor-pointer border-t border-slate-700 hover:bg-slate-700 ${
                          selected === r.id ? 'bg-slate-700' : ''
                        }`}
                      >
                        <td className="px-3 py-2">{new Date(r.received_at).toLocaleTimeString()}</td>
                        <td className="px-3 py-2">{r.id}</td>
                        <td className="px-3 py-2">{r.device_id}</td>
                        <td className="px-3 py-2">{fmt(r.rssi, ' dBm')}</td>
                        <td className="px-3 py-2">{fmt(r.gateway_latency, ' ms')}</td>
                        <td className="px-3 py-2">{fmt(r.internet_latency, ' ms')}</td>
                        <td className="px-3 py-2">{fmt(r.dns_time, ' ms')}</td>
                        <td className="px-3 py-2">{fmt(r.packet_loss, ' %')}</td>
                        <td className="px-3 py-2">{r.packet_matched ? 'yes' : 'no'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <>
              <h2 className="mb-2 text-lg font-semibold">Diagnosis history</h2>
              <div className="overflow-x-auto rounded-lg bg-slate-800">
                <table className="w-full text-left text-sm">
                  <thead className="text-xs uppercase text-slate-400">
                    <tr>
                      {['Time', 'Reading', 'Fault', 'Severity', 'Verified', 'Unusual'].map((h) => (
                        <th key={h} className="px-3 py-2">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((h) => (
                      <tr
                        key={h.id}
                        onClick={() => showStored(h)}
                        className={`cursor-pointer border-t border-slate-700 hover:bg-slate-700 ${
                          selected === h.telemetry_id ? 'bg-slate-700' : ''
                        }`}
                      >
                        <td className="px-3 py-2">{new Date(h.created_at).toLocaleTimeString()}</td>
                        <td className="px-3 py-2">{h.telemetry_id}</td>
                        <td className="px-3 py-2">{h.fault_label.replaceAll('_', ' ')}</td>
                        <td className="px-3 py-2"><SeverityBadge severity={h.severity} /></td>
                        <td className="px-3 py-2">{h.verified ? 'yes' : 'no'}</td>
                        <td className="px-3 py-2">{h.is_anomaly ? 'yes' : 'no'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {history.length === 0 && (
                  <p className="p-4 text-sm text-slate-400">
                    No diagnoses saved yet. Click a reading on the Live tab, or use the demo bar.
                  </p>
                )}
              </div>
            </>
          )}
        </section>

        <aside className="rounded-lg bg-slate-800 p-4">
          <h2 className="mb-2 text-lg font-semibold">Diagnosis</h2>

          {!selected && !diagError && (
            <p className="text-sm text-slate-400">
              Click a reading or a history row, use the Explain button, or try the demo bar, to see
              the explanation from the diagnosis agent.
            </p>
          )}
          {diagLoading && <p className="text-sm text-slate-400">Analysing reading {selected}...</p>}
          {diagError && (
            <p className="rounded bg-rose-900/60 p-2 text-sm text-rose-200">
              {selected ? `Reading ${selected}: ` : ''}
              {diagError}
            </p>
          )}

          {diag && (
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xl font-semibold">{diag.fault_label.replaceAll('_', ' ')}</span>
                <SeverityBadge severity={diag.severity} />
                <span
                  className={`rounded px-2 py-0.5 text-xs ${diag.verified ? 'bg-emerald-700' : 'bg-rose-700'}`}
                >
                  {diag.verified ? 'verified' : 'check failed'}
                </span>
              </div>
              <div className="mt-1 text-xs text-slate-400">
                Reading {diag.telemetry_id}, confidence {Math.round(diag.confidence * 100)}%
                {diag.stored && diag.created_at
                  ? `, saved ${new Date(diag.created_at).toLocaleString()}`
                  : ''}
              </div>
              <pre className="mt-3 whitespace-pre-wrap font-sans text-sm leading-relaxed text-slate-200">
                {diag.explanation}
              </pre>
              {(diag.sources ?? []).length > 0 && (
                <div className="mt-3 text-xs text-slate-500">Sources: {diag.sources.join(', ')}</div>
              )}
            </div>
          )}
        </aside>
      </div>
    </div>
  )
}
