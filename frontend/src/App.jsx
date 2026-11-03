import { useCallback, useEffect, useState } from 'react'

const API = 'http://127.0.0.1:8000'
const POLL_MS = 5000

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

export default function App() {
  const [latest, setLatest] = useState(null)
  const [rows, setRows] = useState([])
  const [error, setError] = useState(null)
  const [updated, setUpdated] = useState(null)

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

  useEffect(() => {
    load()
    const timer = setInterval(load, POLL_MS)
    return () => clearInterval(timer)
  }, [load])

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

      {!rec && !error && (
        <p className="mt-8 text-slate-400">No readings yet. Run the simulator or the ESP32 node.</p>
      )}

      {rec && (
        <section className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
          <div className="col-span-2 rounded-lg bg-slate-800 p-4">
            <div className="text-xs uppercase tracking-wide text-slate-400">Current state</div>
            {pred ? (
              <>
                <div className="mt-1 flex items-center gap-3">
                  <span className="text-2xl font-semibold">{pred.fault_label.replaceAll('_', ' ')}</span>
                  <span
                    className={`rounded px-2 py-0.5 text-sm ${SEVERITY_STYLE[pred.severity] ?? 'bg-slate-600'}`}
                  >
                    {pred.severity}
                  </span>
                </div>
                <div className="mt-1 text-xs text-slate-400">
                  Confidence {Math.round(pred.confidence * 100)}%
                  {pred.is_anomaly ? ' - unusual compared with normal behaviour' : ''}
                </div>
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

      <section className="mt-8">
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
                <tr key={r.id} className="border-t border-slate-700">
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
      </section>
    </div>
  )
}
