import { useEffect, useState } from 'react'

const API = 'http://127.0.0.1:8000'

export default function App() {
  const [status, setStatus] = useState('Checking...')

  useEffect(() => {
    fetch(`${API}/health`)
      .then((r) => r.json())
      .then((d) => setStatus(d.status === 'ok' ? 'Backend connected' : 'Unexpected response'))
      .catch(() => setStatus('Backend not reachable'))
  }, [])

  const ok = status === 'Backend connected'

  return (
    <div className="min-h-screen bg-slate-900 p-8 text-slate-100">
      <h1 className="text-3xl font-bold">NetMind</h1>
      <p className="text-slate-400">Network monitoring dashboard</p>
      <span
        className={`mt-6 inline-block rounded px-3 py-1 text-sm ${
          ok ? 'bg-emerald-600' : 'bg-rose-600'
        }`}
      >
        {status}
      </span>
    </div>
  )
}
